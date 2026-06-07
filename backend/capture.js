const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    const browser = await puppeteer.launch({ headless: 'new' });
    const page = await browser.newPage();
    await page.setViewport({ width: 1440, height: 900 });

    try {
        await page.goto('http://localhost:8000', { waitUntil: 'networkidle0' });
        
        // Wait a bit for initial render
        await new Promise(r => setTimeout(r, 2000));
        
        // 1. Dashboard
        await page.screenshot({ path: '../docs/assets/dashboard.png' });

        // Click first candidate to open Reasoning Chamber
        await page.evaluate(() => {
            const firstCand = document.querySelector('.tile-transition');
            if(firstCand) firstCand.click();
        });
        await new Promise(r => setTimeout(r, 1000));
        
        // 2. Reasoning Chamber
        await page.screenshot({ path: '../docs/assets/reasoning.png' });
        
        // 3. Discovery Event 
        await page.screenshot({ path: '../docs/assets/discovery_event.png' });
        
        // 4. Blind Review
        await page.evaluate(() => {
            const btn = document.getElementById('btn-blind-review');
            if(btn) btn.click();
        });
        await new Promise(r => setTimeout(r, 1000));
        await page.screenshot({ path: '../docs/assets/blind_review.png' });

        // 5. Competency Graph
        await page.evaluate(() => {
            const tab = document.querySelector('.nav-item[data-view="competency"]');
            if(tab) tab.click();
        });
        await new Promise(r => setTimeout(r, 1000));
        await page.screenshot({ path: '../docs/assets/graph.png' });
        
        // 6. GIF placeholder
        fs.copyFileSync('../docs/assets/dashboard.png', '../docs/assets/evidra-demo.gif');
        
        console.log("Screenshots captured!");
    } catch (e) {
        console.error(e);
    } finally {
        await browser.close();
    }
})();
