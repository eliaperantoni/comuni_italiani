from bs4 import BeautifulSoup
import aiocsv
import aiofiles
import aiohttp
import asyncio
import tqdm

N_FETCHERS = 4

FILE_I = "abitanti_2019_2020.csv"
FILE_O = "output.csv"
FILE_E = "errors.csv"

URL = "http://www.comuni-italiani.it/{}/{}/amm.html"


def init_progress():
    with open(FILE_I, "r") as f:
        # Only an estimate because we have duplicates
        num_lines_estimate = sum(1 for _ in f)

        # Don't count final empty line
        num_lines_estimate -= 1

        return tqdm.tqdm(total=num_lines_estimate)


progress = init_progress()

# Set of istat codes of already seen town (used to remove duplicates)
seen = set()


def extract_mayor(text: str) -> str:
    bs = BeautifulSoup(text, "html.parser")

    header_td = bs.find("td", text="Sindaco")
    header_tr = header_td.parent
    mayor_tr = header_tr.find_next_sibling("tr")
    mayor_td = next(mayor_tr.children)
    mayor_b = mayor_td.find("b")
    mayor = mayor_b.string

    return mayor


async def run_reader(i: asyncio.Queue):
    async with aiofiles.open(FILE_I, "r") as f:
        csv_reader = aiocsv.AsyncReader(f, delimiter=";")

        # Skip header
        await csv_reader.__anext__()

        async for row in csv_reader:
            istat_code = row[0]

            # Is this a duplicate town? If so, skip
            if istat_code in seen:
                # This line does not count so we have to decrease the estimate
                progress.total -= 1
                progress.update(0)

                continue

            # Otherwise add to the set of seen towns
            seen.add(istat_code)

            # And send to input queue
            await i.put(istat_code)


async def run_fetcher(i: asyncio.Queue, o: asyncio.Queue, sess: aiohttp.ClientSession):
    while True:
        # Get istat code from input queue
        istat_code = await i.get()

        # Make the HTTP request
        async with sess.get(URL.format(istat_code[:3], istat_code[3:])) as resp:
            # If request didn't go well, skip it (but remember to mark input queue item as processed)
            if resp.status != 200:
                # Some error, don't count towards total
                progress.total -= 1
                progress.update(0)

                i.task_done()

                continue

            text = await resp.text()

            try:
                mayor = extract_mayor(text)
            except:
                # This line does not count so we have to decrease the estimate
                progress.total -= 1
                progress.update(0)

                i.task_done()

                continue

            await o.put((istat_code, mayor))
            i.task_done()


async def run_writer(o: asyncio.Queue):
    async with aiofiles.open(FILE_O, "w") as f:
        writer = aiocsv.AsyncWriter(f)

        while True:
            (istat_code, mayor) = await o.get()
            await writer.writerow([istat_code, mayor])

            progress.update()

            o.task_done()


async def main():
    i = asyncio.Queue(100)
    o = asyncio.Queue(100)

    writer = asyncio.create_task(run_writer(o))

    async with aiohttp.ClientSession() as sess:
        fetchers = [run_fetcher(i, o, sess) for _ in range(N_FETCHERS)]
        fetchers = [asyncio.create_task(fetcher) for fetcher in fetchers]

        reader = asyncio.create_task(run_reader(i))

        await reader
        await i.join()
        await o.join()

    for fetcher in fetchers:
        fetcher.cancel()

    writer.cancel()


if __name__ == '__main__':
    asyncio.run(main())
