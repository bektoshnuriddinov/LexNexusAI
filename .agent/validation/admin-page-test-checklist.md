# Admin Page Test Checklist

**Date:** __________  **Tester:** __________

## Pre-Test Setup
- [ ] Frontend running: http://localhost:5173
- [ ] Backend running: http://localhost:8000
- [ ] Browser opened (Chrome/Firefox recommended)

---

## Test 1: Admin Login
- [ ] Navigate to http://localhost:5173
- [ ] Sign in with: creator@rag.com / M+T!kV3v2d_xn/p
- [ ] Login succeeds

---

## Test 2: Admin Page Access
- [ ] Navigate to http://localhost:5173/admin
- [ ] Page loads (no "Access Denied")
- [ ] "User Management" title visible
- [ ] "Create New User" form visible
- [ ] "All Users" list visible
- [ ] Screenshot taken: ________________

---

## Test 3: User List Display
- [ ] User list shows existing users
- [ ] Email addresses visible
- [ ] Created dates visible
- [ ] Admin badges visible (if applicable)
- [ ] List is sorted (newest first)
- [ ] Screenshot taken: ________________

---

## Test 4: Create Non-Admin User
- [ ] Enter email: admintest@example.com
- [ ] Enter password: testpass123
- [ ] Leave admin checkbox UNCHECKED
- [ ] Click "Create User"
- [ ] Button shows "Creating..." briefly
- [ ] Form clears after creation
- [ ] User appears in list
- [ ] No admin badge on new user
- [ ] Screenshot taken: ________________

---

## Test 5: Create Admin User
- [ ] Enter email: admintest2@example.com
- [ ] Enter password: testpass123
- [ ] CHECK admin checkbox
- [ ] Click "Create User"
- [ ] User appears in list
- [ ] Blue "Admin" badge visible
- [ ] Screenshot taken: ________________

---

## Test 6: Error - Duplicate Email
- [ ] Try to create: admintest@example.com again
- [ ] Error message displays (red banner)
- [ ] Form is NOT cleared
- [ ] User list unchanged
- [ ] Screenshot taken: ________________

---

## Test 7: Validation - Invalid Email
- [ ] Enter email: notanemail
- [ ] Try to submit
- [ ] Browser validation blocks submission
- [ ] HTML5 error message appears

---

## Test 8: Validation - Short Password
- [ ] Enter email: test3@example.com
- [ ] Enter password: 123 (only 3 chars)
- [ ] Try to submit
- [ ] Browser validation blocks submission
- [ ] Message: "Please lengthen this text"

---

## Test 9: Non-Admin Access Control
- [ ] Sign out from admin account
- [ ] Sign in with: test@test.com / M+T!kV3v2d_xn/p
- [ ] Navigate to http://localhost:5173/admin
- [ ] "Access Denied" card displays
- [ ] Message: "You need admin access to view this page"
- [ ] No user management interface visible
- [ ] Screenshot taken: ________________

---

## Test Results Summary

| Test | Status |
|------|--------|
| 1. Admin Login | [ ] Pass [ ] Fail |
| 2. Admin Page Access | [ ] Pass [ ] Fail |
| 3. User List Display | [ ] Pass [ ] Fail |
| 4. Create Non-Admin User | [ ] Pass [ ] Fail |
| 5. Create Admin User | [ ] Pass [ ] Fail |
| 6. Duplicate Email Error | [ ] Pass [ ] Fail |
| 7. Invalid Email Validation | [ ] Pass [ ] Fail |
| 8. Short Password Validation | [ ] Pass [ ] Fail |
| 9. Non-Admin Access Control | [ ] Pass [ ] Fail |

**Overall Result:** [ ] ALL PASS [ ] SOME FAILURES

---

## Issues Found

**Issue 1:**
Description: _________________________________
Severity: [ ] Critical [ ] High [ ] Medium [ ] Low

**Issue 2:**
Description: _________________________________
Severity: [ ] Critical [ ] High [ ] Medium [ ] Low

**Issue 3:**
Description: _________________________________
Severity: [ ] Critical [ ] High [ ] Medium [ ] Low

---

## Cleanup Tasks
- [ ] Delete test user: admintest@example.com
- [ ] Delete test user: admintest2@example.com
- [ ] Archive screenshots
- [ ] Document findings

---

## Notes

_______________________________________________________
_______________________________________________________
_______________________________________________________
_______________________________________________________
_______________________________________________________

---

**Test Complete:** [ ] Yes [ ] No
**Sign-off:** __________________ Date: __________
