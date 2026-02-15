const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  try {
    console.log('\n=== DOCUMENT DEDUPLICATION TEST ===\n');
    
    // Step 1: Navigate
    console.log('[1/7] Navigating to localhost:5173...');
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    console.log('✓ Page loaded');
    
    // Step 2: Sign in
    console.log('[2/7] Signing in as test@test.com...');
    await page.fill('input[type="email"]', 'test@test.com');
    await page.fill('input[type="password"]', 'M+T!kV3v2d_xn/p');
    await page.click('button:has-text("Sign in")');
    await page.waitForURL('**', { timeout: 20000 });
    await page.waitForTimeout(2000);
    console.log('✓ Signed in');
    
    // Step 3: Go to Documents
    console.log('[3/7] Navigating to Documents page...');
    const docLink = page.locator('a, button').filter({ hasText: /^Documents$/ }).first();
    await docLink.click();
    await page.waitForURL('**/documents');
    await page.waitForTimeout(2000);
    console.log('✓ On Documents page');
    
    // Step 4: Count initial documents
    console.log('[4/7] Counting initial documents...');
    const count1 = await page.locator('tbody tr').count();
    console.log(`✓ Initial count: ${count1}`);
    
    // Step 5: Upload file first time
    console.log('[5/7] Uploading test_document.txt (1st time)...');
    const fileInput = page.locator('input[type="file"]');
    const filePath = '.agent/validation/fixtures/test_document.txt';
    await fileInput.setInputFiles(filePath);
    
    // Wait for status to become "completed"
    console.log('  Waiting for processing (max 30s)...');
    let completed = false;
    for (let i = 0; i < 15; i++) {
      await page.waitForTimeout(2000);
      const tbody = await page.locator('tbody').textContent();
      if (tbody.includes('completed')) {
        completed = true;
        break;
      }
      process.stdout.write('.');
    }
    console.log(completed ? '\n✓ Upload completed' : '\n✗ Upload timeout');
    
    const count2 = await page.locator('tbody tr').count();
    console.log(`✓ Document count after 1st upload: ${count2}`);
    
    // Take screenshot
    await page.screenshot({ path: 'after-first-upload.png' });
    console.log('  Screenshot: after-first-upload.png');
    
    // Step 6: Upload same file again
    console.log('[6/7] Uploading test_document.txt AGAIN (2nd time - SAME FILE)...');
    const fileInput2 = page.locator('input[type="file"]');
    await fileInput2.setInputFiles(filePath);
    await page.waitForTimeout(3000);
    console.log('✓ Re-upload requested');
    
    const count3 = await page.locator('tbody tr').count();
    console.log(`✓ Document count after 2nd upload: ${count3}`);
    
    // Take screenshot
    await page.screenshot({ path: 'after-second-upload.png' });
    console.log('  Screenshot: after-second-upload.png');
    
    // Step 7: Analyze results
    console.log('[7/7] Analyzing results...\n');
    console.log('=== RESULTS ===');
    console.log(`Initial count:     ${count1}`);
    console.log(`After 1st upload:  ${count2}`);
    console.log(`After 2nd upload:  ${count3}`);
    console.log('');
    
    if (count2 === count3) {
      console.log('✓✓✓ DEDUPLICATION WORKING ✓✓✓');
      console.log('The same document was returned, no duplicate created');
    } else {
      console.log('✗✗✗ DEDUPLICATION FAILED ✗✗✗');
      console.log('A duplicate document was created');
    }
    
  } catch (error) {
    console.error('Test error:', error.message);
    console.error(error.stack);
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
  }
})();
