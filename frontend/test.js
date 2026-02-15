const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('1. Navigating to http://localhost:5173...');
    await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded', timeout: 15000 });
    
    // Check if on auth page
    const authTitle = await page.title();
    console.log('Page title:', authTitle);
    
    // Sign in
    console.log('2. Filling in email and password...');
    await page.fill('input[type="email"]', 'test@test.com');
    await page.fill('input[type="password"]', 'M+T!kV3v2d_xn/p');
    
    console.log('3. Clicking Sign In button...');
    await page.click('button:has-text("Sign in")');
    
    // Wait for navigation to complete
    console.log('4. Waiting for authentication to complete...');
    await page.waitForURL('**/chat', { timeout: 15000 });
    await page.waitForTimeout(2000);
    
    console.log('5. Navigating to Documents page...');
    // Click Documents link
    await page.click('a:has-text("Documents"), button:has-text("Documents")');
    await page.waitForURL('**/documents', { timeout: 10000 });
    await page.waitForTimeout(2000);
    
    // Take screenshot of initial state
    console.log('Screenshot 1: Taken before upload');
    await page.screenshot({ path: '/tmp/before-upload.png' });
    
    // Get initial document count
    const docRows1 = await page.$$('table tbody tr');
    const initialCount = docRows1.length;
    console.log(`6. Initial document count: ${initialCount}`);
    
    // Upload file
    console.log('7. Uploading test_document.txt (first time)...');
    const fileInput = await page.$('input[type="file"]');
    if (!fileInput) {
      console.log('File input not found');
    } else {
      const testFilePath = path.resolve('../.agent/validation/fixtures/test_document.txt');
      console.log(`   File path: ${testFilePath}`);
      await fileInput.setInputFiles(testFilePath);
      await page.waitForTimeout(2000);
    }
    
    // Wait for document to appear
    console.log('8. Waiting for document status to show "completed"...');
    let maxWait = 0;
    let status = 'pending';
    while (status !== 'completed' && maxWait < 60) {
      await page.waitForTimeout(2000);
      maxWait += 2;
      const cells = await page.$$eval('td', els => els.map(e => e.textContent?.trim() || ''));
      status = cells.includes('completed') ? 'completed' : status;
      console.log(`   Status check (${maxWait}s): ${status}`);
    }
    
    console.log('Screenshot 2: Taken after first upload');
    await page.screenshot({ path: '/tmp/after-first-upload.png' });
    
    // Count documents after first upload
    const docRows2 = await page.$$('table tbody tr');
    const countAfterFirst = docRows2.length;
    console.log(`9. Document count after first upload: ${countAfterFirst}`);
    
    // Upload same file again
    console.log('10. Uploading test_document.txt (second time - SAME FILE)...');
    const fileInput2 = await page.$('input[type="file"]');
    if (fileInput2) {
      const testFilePath = path.resolve('../.agent/validation/fixtures/test_document.txt');
      await fileInput2.setInputFiles(testFilePath);
      await page.waitForTimeout(3000);
    }
    
    console.log('Screenshot 3: Taken after second upload');
    await page.screenshot({ path: '/tmp/after-second-upload.png' });
    
    // Count documents after second upload
    const docRows3 = await page.$$('table tbody tr');
    const countAfterSecond = docRows3.length;
    console.log(`11. Document count after second upload: ${countAfterSecond}`);
    
    // Results
    console.log('\n=== DEDUPLICATION TEST RESULTS ===');
    console.log(`Initial count: ${initialCount}`);
    console.log(`After 1st upload: ${countAfterFirst}`);
    console.log(`After 2nd upload: ${countAfterSecond}`);
    
    if (countAfterFirst === countAfterSecond) {
      console.log('\n✓ DEDUPLICATION WORKING: Same document returned, no duplicate created');
    } else {
      console.log('\n✗ DEDUPLICATION NOT WORKING: Duplicate document was created');
    }
    
  } catch (error) {
    console.error('Error during test:', error.message);
    console.error(error.stack);
  } finally {
    await page.waitForTimeout(5000);
    await browser.close();
  }
})();
