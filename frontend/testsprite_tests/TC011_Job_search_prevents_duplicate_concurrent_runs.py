import asyncio
from playwright import async_api
from playwright.async_api import expect

async def run_test():
    pw = None
    browser = None
    context = None

    try:
        # Start a Playwright session in asynchronous mode
        pw = await async_api.async_playwright().start()

        # Launch a Chromium browser in headless mode with custom arguments
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--window-size=1280,720",         # Set the browser window size
                "--disable-dev-shm-usage",        # Avoid using /dev/shm which can cause issues in containers
                "--ipc=host",                     # Use host-level IPC for better stability
                "--single-process"                # Run the browser in a single process mode
            ],
        )

        # Create a new browser context (like an incognito window)
        context = await browser.new_context()
        context.set_default_timeout(5000)

        # Open a new page in the browser context
        page = await context.new_page()

        # Interact with the page elements to simulate user flow
        # -> Navigate to http://localhost:5173
        await page.goto("http://localhost:5173")
        
        # -> Click the 'Sign in' link to reach the login page so we can authenticate and continue the workflow.
        frame = context.pages[-1]
        # Click element
        elem = frame.locator('xpath=/html/body/div/header/div/a').nth(0)
        await asyncio.sleep(3); await elem.click()
        
        # -> Click the 'Jobs' navigation link to open the Jobs page and locate the job search controls so we can start a job search and then attempt to trigger a second search while the first is running.
        frame = context.pages[-1]
        # Click element
        elem = frame.locator('xpath=/html/body/div/header/div/nav/a[5]').nth(0)
        await asyncio.sleep(3); await elem.click()
        
        # -> Enter a search query into the Jobs page search field and submit it (press Enter) to start a job search, so we can then attempt a second search while the first is running.
        frame = context.pages[-1]
        # Input text
        elem = frame.locator('xpath=/html/body/div/main/div/div[2]/div/input').nth(0)
        await asyncio.sleep(3); await elem.fill('ML Engineer')
        
        # --> Assertions to verify final state
        frame = context.pages[-1]
        assert await frame.locator("xpath=//*[contains(., 'Searching jobs...')]").nth(0).is_visible(), "The UI should show a single job search in progress indicator after triggering a search and prevent starting a second concurrent search."
        await asyncio.sleep(5)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()

asyncio.run(run_test())
    