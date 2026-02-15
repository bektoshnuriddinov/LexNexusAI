# Admin User Management Page - Manual Test Report

**Test Date:** 2026-02-14
**Tester:** Manual Testing Required
**Frontend URL:** http://localhost:5173
**Backend URL:** http://localhost:8000

## Test Credentials

**Admin User:**
- Email: creator@rag.com
- Password: M+T!kV3v2d_xn/p

## Test Objectives

Validate the admin user management page functionality including:
1. Authentication and access control
2. Admin page rendering
3. User creation functionality
4. User list display
5. Error handling

---

## Test Execution Steps

### Step 1: Navigate to Application
**Action:** Open browser and navigate to http://localhost:5173

**Expected Result:**
- Application loads successfully
- Landing page or login page is displayed

**Status:** [ ] PASS / [ ] FAIL
**Screenshot:** (Attach screenshot here)
**Notes:**

---

### Step 2: Sign In as Admin
**Action:**
1. Click on sign-in button/link
2. Enter email: creator@rag.com
3. Enter password: M+T!kV3v2d_xn/p
4. Click Sign In

**Expected Result:**
- Sign in succeeds without errors
- User is redirected to main application
- User avatar/menu shows logged in state

**Status:** [ ] PASS / [ ] FAIL
**Screenshot:** (Attach screenshot here)
**Notes:**

---

### Step 3: Navigate to Admin Page
**Action:** Navigate to http://localhost:5173/admin

**Expected Result:**
- Admin page loads successfully (not "Access Denied")
- Page displays "User Management" title
- "Create New User" form is visible with:
  - Email input field
  - Password input field
  - Admin privileges checkbox
  - Create User button
- "All Users" section is visible

**Status:** [ ] PASS / [ ] FAIL
**Screenshot:** (Attach screenshot here)
**Notes:**

---

### Step 4: Verify Initial User List
**Action:** Observe the "All Users" list section

**Expected Result:**
- List of existing users is displayed
- Each user shows:
  - Email address
  - Created date
  - "Admin" badge (if user is admin)
- Users are sorted by creation date (newest first)

**Status:** [ ] PASS / [ ] FAIL
**Screenshot:** (Attach screenshot here)
**User Count:** ___
**Notes:**

---

### Step 5: Create Test User (Non-Admin)
**Action:**
1. In "Create New User" form, enter:
   - Email: admintest@example.com
   - Password: testpass123
   - Admin privileges: UNCHECKED (leave unchecked)
2. Click "Create User" button

**Expected Result:**
- Button shows "Creating..." state briefly
- No error message appears
- Form fields are cleared after successful creation
- User list automatically refreshes
- New user "admintest@example.com" appears at the top of the list
- New user does NOT have "Admin" badge

**Status:** [ ] PASS / [ ] FAIL
**Screenshot:** (Attach screenshot here)
**Notes:**

---

### Step 6: Verify New User in List
**Action:** Scroll through the "All Users" list

**Expected Result:**
- "admintest@example.com" is visible in the list
- Email is displayed correctly
- Created date is today's date
- No "Admin" badge is shown for this user

**Status:** [ ] PASS / [ ] FAIL
**Screenshot:** (Attach screenshot here)
**Notes:**

---

### Step 7: Create Test User (With Admin)
**Action:**
1. In "Create New User" form, enter:
   - Email: admintest2@example.com
   - Password: testpass123
   - Admin privileges: CHECKED
2. Click "Create User" button

**Expected Result:**
- User is created successfully
- New user appears in list with "Admin" badge

**Status:** [ ] PASS / [ ] FAIL
**Screenshot:** (Attach screenshot here)
**Notes:**

---

### Step 8: Test Error Handling - Duplicate Email
**Action:**
1. Try to create user with email: admintest@example.com (already exists)
2. Password: testpass123
3. Click "Create User"

**Expected Result:**
- Error message is displayed (red/destructive background)
- Error message indicates user already exists or similar
- Form is not cleared
- User list is not affected

**Status:** [ ] PASS / [ ] FAIL
**Screenshot:** (Attach screenshot here)
**Error Message:** ___
**Notes:**

---

### Step 9: Test Error Handling - Invalid Email
**Action:**
1. Enter email: notanemail
2. Password: testpass123
3. Try to click "Create User"

**Expected Result:**
- Browser validation prevents form submission
- HTML5 email validation message appears

**Status:** [ ] PASS / [ ] FAIL
**Screenshot:** (Attach screenshot here)
**Notes:**

---

### Step 10: Test Error Handling - Short Password
**Action:**
1. Enter email: test3@example.com
2. Password: 123 (less than 6 characters)
3. Try to click "Create User"

**Expected Result:**
- Browser validation prevents form submission
- Message indicates password must be at least 6 characters

**Status:** [ ] PASS / [ ] FAIL
**Screenshot:** (Attach screenshot here)
**Notes:**

---

### Step 11: Test Non-Admin Access
**Action:**
1. Sign out from creator@rag.com
2. Sign in with: test@test.com / M+T!kV3v2d_xn/p (non-admin user)
3. Navigate to http://localhost:5173/admin

**Expected Result:**
- Page shows "Access Denied" card
- Message: "You need admin access to view this page"
- No user management interface is visible

**Status:** [ ] PASS / [ ] FAIL
**Screenshot:** (Attach screenshot here)
**Notes:**

---

## Backend API Verification (Optional)

If you want to verify the backend API directly, you can use these curl commands after obtaining a valid access token.

### Get Admin User Info
```bash
# First, get access token from browser console:
# supabase.auth.getSession().then(({data}) => console.log(data.session.access_token))

export TOKEN="your_access_token_here"

# Test /auth/me endpoint
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "id": "user-id-here",
  "email": "creator@rag.com",
  "is_admin": true
}
```

### List All Users
```bash
curl -X GET http://localhost:8000/admin/users \
  -H "Authorization: Bearer $TOKEN"
```

Expected response: Array of users with id, email, is_admin, created_at

### Create User via API
```bash
curl -X POST http://localhost:8000/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "apitest@example.com",
    "password": "testpass123",
    "is_admin": false
  }'
```

Expected response: Created user object with 201 status

---

## Test Summary

| Test Step | Status | Notes |
|-----------|--------|-------|
| 1. Navigate to Application | [ ] PASS / [ ] FAIL | |
| 2. Sign In as Admin | [ ] PASS / [ ] FAIL | |
| 3. Navigate to Admin Page | [ ] PASS / [ ] FAIL | |
| 4. Verify Initial User List | [ ] PASS / [ ] FAIL | |
| 5. Create Test User (Non-Admin) | [ ] PASS / [ ] FAIL | |
| 6. Verify New User in List | [ ] PASS / [ ] FAIL | |
| 7. Create Test User (With Admin) | [ ] PASS / [ ] FAIL | |
| 8. Test Duplicate Email Error | [ ] PASS / [ ] FAIL | |
| 9. Test Invalid Email Error | [ ] PASS / [ ] FAIL | |
| 10. Test Short Password Error | [ ] PASS / [ ] FAIL | |
| 11. Test Non-Admin Access | [ ] PASS / [ ] FAIL | |

**Overall Result:** [ ] PASS / [ ] FAIL

---

## Issues Found

### Issue 1
**Severity:** [ ] Critical / [ ] High / [ ] Medium / [ ] Low
**Description:**
**Steps to Reproduce:**
**Expected Behavior:**
**Actual Behavior:**
**Screenshot:**

### Issue 2
**Severity:** [ ] Critical / [ ] High / [ ] Medium / [ ] Low
**Description:**
**Steps to Reproduce:**
**Expected Behavior:**
**Actual Behavior:**
**Screenshot:**

---

## Component Analysis

### Frontend Component: AdminPage.tsx
**Location:** `C:\Users\Defender\programm\innovatsiya\RAG2\frontend\src\pages\AdminPage.tsx`

**Key Features:**
- Access control check (lines 92-103): Displays "Access Denied" if user is not admin
- User list loading (lines 30-51): Fetches users from `/admin/users` endpoint
- User creation form (lines 53-90): Posts to `/admin/users` endpoint
- Real-time updates: Automatically refreshes user list after creation
- Error handling: Displays error messages in red destructive style

**API Endpoints Used:**
- GET `/admin/users` - List all users
- POST `/admin/users` - Create new user

### Backend Router: admin.py
**Location:** `C:\Users\Defender\programm\innovatsiya\RAG2\backend\app\routers\admin.py`

**Key Features:**
- Admin-only access via `get_admin_user` dependency
- Uses Supabase Admin Client for privileged operations
- Creates user in both auth.users and user_profiles tables
- Rollback mechanism if profile creation fails
- Auto-confirms email for created users

**Validation:**
- Email validation via Pydantic EmailStr
- Password minimum length enforced
- Transaction safety with rollback

---

## Recommendations

1. **Security:** Admin access control is properly implemented at both frontend and backend levels
2. **UX:** Form validation provides good user feedback
3. **Data Integrity:** Rollback mechanism ensures consistency between auth and profile tables
4. **Testing:** Consider automated E2E tests using Playwright for regression testing

---

## Cleanup Steps (After Testing)

To clean up test users created during testing:

1. Sign in as admin (creator@rag.com)
2. Use Supabase dashboard to delete test users:
   - admintest@example.com
   - admintest2@example.com
   - apitest@example.com (if created)

Or use Supabase Admin Panel directly to manage users.
