# 💳 Test Card Numbers - Quick Reference

## ✅ You're in Stripe Test Mode - Safe to Test!

Your `.env` has `sk_test_` keys = **No real money will be charged**

---

## 🎯 Most Common Test Cards

### ✅ Success
```
4242 4242 4242 4242
```
**Use this for normal testing**

### ❌ Declined
```
4000 0000 0000 0002
```
**Test error handling**

### 💰 Insufficient Funds
```
4000 0000 0000 9995
```
**Test insufficient balance**

### 🔒 Authentication Required
```
4000 0025 0000 3155
```
**Test 3D Secure flow**

---

## 📝 Required Fields

- **Expiry**: Any future date (e.g., `12/25`)
- **CVC**: Any 3 digits (e.g., `123`)
- **ZIP**: Any 5 digits (e.g., `12345`)

---

## 🎓 Quick Test Flow

1. Search flights/hotels (IAD → JFK)
2. Select and go to checkout
3. Use card: **4242 4242 4242 4242**
4. Exp: **12/25**, CVC: **123**
5. Complete booking ✅

**No real money charged!**

---

## 📊 View Test Results

- **Stripe Dashboard**: https://dashboard.stripe.com/test/payments
- **Admin Panel**: http://172.168.1.95:8109/admin/payments/payment/

---

## 🔗 Full Guide

See `TESTING_BOOKINGS.md` for complete testing documentation.
