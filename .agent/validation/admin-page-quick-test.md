# Admin Page Quick Test Guide

## Prerequisites
- Frontend running at: http://localhost:5173
- Backend running at: http://localhost:8000
- Services verified: Both are currently running

## Quick Test (5 minutes)

### 1. Login as Admin
1. Open: http://localhost:5173
2. Sign in with:
   - **Email:** creator@rag.com
   - **Password:** M+T!kV3v2d_xn/p

### 2. Navigate to Admin Page
1. Go to: http://localhost:5173/admin
2. Verify you see:
   - "User Management" title
   - "Create New User" form
   - "All Users" list

### 3. Create Test User
1. Fill form:
   - **Email:** admintest@example.com
   - **Password:** testpass123
   - **Admin privileges:** Unchecked
2. Click "Create User"
3. Verify:
   - Form clears
   - New user appears at top of list
   - No "Admin" badge shown

### 4. Check Access Control
1. Sign out
2. Sign in as: test@test.com / M+T!kV3v2d_xn/p
3. Navigate to: http://localhost:5173/admin
4. Verify: "Access Denied" message appears

## Expected Results Summary

✅ **PASS Criteria:**
- Admin can access /admin page
- User creation works and updates list
- Non-admin users see "Access Denied"
- Form validation prevents invalid inputs

❌ **FAIL if:**
- Admin page shows "Access Denied" for creator@rag.com
- User creation fails with error
- Non-admin can access admin page
- New user doesn't appear in list

## Screenshot Checklist

Take screenshots of:
1. [ ] Admin page with "User Management" title and form
2. [ ] "All Users" list with existing users
3. [ ] Form after creating user (should be cleared)
4. [ ] User list with new user "admintest@example.com"
5. [ ] "Access Denied" message for non-admin user

## Cleanup

After testing, delete test user:
- admintest@example.com

(Use Supabase dashboard or create another admin user to delete)
