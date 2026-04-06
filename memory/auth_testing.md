# Auth Testing Playbook

## Step 1: MongoDB Verification
```bash
mongosh
use scoi_database
db.users.find({role: "admin"}).pretty()
db.users.findOne({role: "admin"}, {password_hash: 1})
```

Verify:
- bcrypt hash starts with `$2b$`
- indexes exist on users.email (unique), login_attempts.identifier, password_reset_tokens.expires_at (TTL)

## Step 2: API Testing with External URL

Get backend URL:
```bash
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
echo "Testing with: $API_URL"
```

Test login:
```bash
curl -c /tmp/scoi_cookies.txt -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@scoi.gov.za","password":"SCOI2026!Admin"}'
```

Check cookies:
```bash
cat /tmp/scoi_cookies.txt
```

Test /me endpoint:
```bash
curl -b /tmp/scoi_cookies.txt "$API_URL/api/auth/me"
```

## Expected Behavior
- Login should return user object with id, email, name, role
- Cookies file should contain access_token and refresh_token
- /me endpoint should return same user using cookies
