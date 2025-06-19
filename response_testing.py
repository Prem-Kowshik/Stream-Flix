import aiohttp
import asyncio
from backoff import expo, on_exception
async def return_video_data():

    async def fetch_category(session, sem, title="Category:Films in the public domain", limit=500):
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": title,
            "cmtype": "page|subcat|file",
            "cmlimit": 5,
            "format": "json"
        }
        
        async with sem:
            async with session.get(
                "https://commons.wikimedia.org/w/api.php",
                params=params
            ) as response:
                return await response.json()

    async def process_subcategories(session, sem, root_category):
        queue = asyncio.Queue()
        video_files = []
        
        async def worker():
            while True:
                category = await queue.get()
                try:
                    data = await fetch_category(session, sem, category)
                    for item in data.get('query', {}).get('categorymembers', []):
                        if item['title'].startswith("File:"):
                            print(f"Found file: {item['title']}")
                            if item["title"].endswith((".webm", ".ogv")):
                                print(f"Adding video file: {item['title']}")
                                video_files.append(item)
                        elif item["title"].startswith("Category:"):
                            print(f"Processing subcategory: {item['title']}")
                            if item["title"] != "Category:Erstwhile Susan (play)" and item["title"] != "Category:Erstwhile Susan":
                                await queue.put(item["title"])
                finally:
                    queue.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(10)]
        await queue.put(root_category)
        await queue.join()
        
        for task in workers:
            task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        
        return video_files

    @on_exception(expo, Exception, max_tries=5)
    async def get_video_properties(session, sem, title):
        params = {
            "action": "query",
            "titles": title,
            "prop": "videoinfo",
            "viprop": "canonicaltitle|url|size|dimensions|duration|thumb",
            "viurlwidth": 320,  # Request 320px wide thumbnail
            "format": "json"
        }

        async with sem:
            async with session.get(
                "https://commons.wikimedia.org/w/api.php",
                params=params
            ) as response:
                return await response.json()


    async def final():
        sem = asyncio.Semaphore(20)  # Wikimedia API rate limit
        async with aiohttp.ClientSession() as session:
            video_files = await process_subcategories(session, sem, "Category:Films in the public domain")
            
            # Process video properties in parallel
            tasks = [get_video_properties(session, sem, item["title"]) 
                    for item in video_files]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            final_l = []

            for result in results:
                try:
                    # Get the first (and only) page object
                    page_data = next(iter(result["query"]["pages"].values()))
                    video_info = page_data.get("videoinfo", [{}])[0]

                    # Flatten and enrich the info
                    video_info["pageid"] = page_data.get("pageid")
                    video_info["title"] = page_data.get("title")

                    # Optional: fallback if thumburl isn't present
                    if "thumburl" not in video_info:
                        video_info["thumburl"] = None

                    final_l.append(video_info)

                except Exception as e:
                    print(f"Error processing result: {e}")

            print(final_l)
            return final_l


    return await final()
asyncio.run(return_video_data())
