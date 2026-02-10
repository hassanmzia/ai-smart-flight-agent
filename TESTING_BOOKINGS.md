# Testing Booking Features Safely - Complete Guide

## ✅ Good News: You're Already in Test Mode!

Your application is configured with **Stripe Test Keys**:
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

The `sk_test_` and `pk_test_` prefixes mean you're using **Stripe's Test Mode** - no real money will ever be charged!

---

## 🧪 Option 1: Stripe Test Mode (Current Setup)

### How It Works
- ✅ **100% Safe** - No real credit cards or money involved
- ✅ **All features work** - Process payments, refunds, subscriptions
- ✅ **Real behavior** - Simulates actual payment flow
- ✅ **Already configured** - Your app uses test keys

### Stripe Test Card Numbers

Use these test credit cards in your booking forms:

#### ✅ Successful Payments
```
Card Number: 4242 4242 4242 4242
Expiry: Any future date (e.g., 12/25)
CVC: Any 3 digits (e.g., 123)
ZIP: Any 5 digits (e.g., 12345)
```

#### ❌ Card Declined
```
Card Number: 4000 0000 0000 0002
Expiry: Any future date
CVC: Any 3 digits
```

#### 🔒 Requires Authentication (3D Secure)
```
Card Number: 4000 0025 0000 3155
Expiry: Any future date
CVC: Any 3 digits
```

#### 💳 Insufficient Funds
```
Card Number: 4000 0000 0000 9995
Expiry: Any future date
CVC: Any 3 digits
```

#### ⏰ Processing Error
```
Card Number: 4000 0000 0000 0119
Expiry: Any future date
CVC: Any 3 digits
```

### More Test Cards
Full list available at: https://stripe.com/docs/testing#cards

---

## 🎯 Option 2: Add Application Test Mode

For even safer testing, we can add an application-level test mode that skips payment processing entirely.

### Implementation:

#### 1. Add Test Mode Setting
Add to `.env`:
```bash
# Test Mode - Skip actual payment processing
BOOKING_TEST_MODE=True
```

Add to `backend/travel_agent/settings.py`:
```python
# Booking Configuration
BOOKING_TEST_MODE = os.environ.get('BOOKING_TEST_MODE', 'False').lower() == 'true'
```

#### 2. Update Payment Processing
Modify `backend/apps/payments/views.py`:

```python
from django.conf import settings

class PaymentViewSet(viewsets.ModelViewSet):
    # ... existing code ...

    def create(self, request):
        """Process a payment."""

        # Check if in test mode
        if settings.BOOKING_TEST_MODE:
            # Create a simulated successful payment
            payment = Payment.objects.create(
                user=request.user,
                booking_id=request.data.get('booking_id'),
                amount=request.data.get('amount'),
                currency=request.data.get('currency', 'USD'),
                status='completed',
                gateway_name='test_mode',
                transaction_id=f"TEST{uuid.uuid4().hex[:12].upper()}",
                gateway_transaction_id='test_transaction',
                gateway_response={'test_mode': True}
            )

            return Response({
                'status': 'success',
                'message': '⚠️ TEST MODE: Payment simulated successfully',
                'payment': PaymentSerializer(payment).data
            })

        # Normal Stripe processing for non-test mode
        # ... existing Stripe integration code ...
```

#### 3. Frontend Indicator
Add a test mode banner to `frontend/src/pages/PaymentPage.tsx`:

```typescript
{process.env.REACT_APP_TEST_MODE === 'true' && (
  <div className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4">
    <p className="font-bold">⚠️ TEST MODE ACTIVE</p>
    <p>No real payments will be processed. All bookings are simulated.</p>
  </div>
)}
```

---

## 🔧 Option 3: Mock Backend (No Payment Gateway)

For unit testing or complete isolation:

### Create Test Booking Service

```python
# backend/apps/bookings/test_service.py

class TestBookingService:
    """Service for creating test bookings without payment processing."""

    @staticmethod
    def create_test_booking(user, booking_data):
        """Create a booking with simulated payment."""

        # Create booking
        booking = Booking.objects.create(
            user=user,
            total_amount=booking_data.get('total_amount'),
            currency='USD',
            status='confirmed',  # Skip pending status
            primary_traveler_name=booking_data.get('traveler_name'),
            primary_traveler_email=booking_data.get('traveler_email'),
            primary_traveler_phone=booking_data.get('traveler_phone'),
            notes='TEST BOOKING - NOT REAL'
        )

        # Create simulated payment
        payment = Payment.objects.create(
            user=user,
            booking=booking,
            amount=booking.total_amount,
            currency='USD',
            status='completed',
            gateway_name='test',
            transaction_id=f"TEST{uuid.uuid4().hex[:8].upper()}"
        )

        return {
            'booking': booking,
            'payment': payment,
            'message': 'Test booking created successfully'
        }
```

---

## 🎓 Testing Workflow

### Recommended Approach

1. **Development & Testing**
   - Use Stripe Test Mode (your current setup)
   - Use test card numbers
   - All features work realistically

2. **Pre-Production**
   - Enable `BOOKING_TEST_MODE=True`
   - Test full booking flow without Stripe
   - Verify UI/UX

3. **Production**
   - Switch to Stripe Live Keys: `sk_live_...` and `pk_live_...`
   - Set `BOOKING_TEST_MODE=False`
   - Ready for real transactions

---

## 📊 Viewing Test Transactions

### Stripe Dashboard
1. Go to: https://dashboard.stripe.com/test/payments
2. Login with your Stripe account
3. View all test payments, refunds, and events
4. **Test data is separate from live data**

### Your Admin Panel
```
http://172.168.1.95:8109/admin/payments/payment/
```
Filter by `gateway_name = 'stripe'` and `status = 'completed'`

---

## 🔒 Security Notes

### Current Setup (Stripe Test Mode)
- ✅ Test keys are in `.env` file (not committed to git)
- ✅ No real payment methods can be saved
- ✅ No real charges can occur
- ⚠️ Don't commit `.env` file to version control

### Before Going Live
- [ ] Switch to Stripe Live Keys
- [ ] Set `DEBUG=False` in settings
- [ ] Enable HTTPS/SSL
- [ ] Set strong `SECRET_KEY`
- [ ] Review payment flow security
- [ ] Test error handling
- [ ] Set up webhook signature verification

---

## 🧪 Example Test Scenarios

### 1. Successful Booking
```
1. Search for flights/hotels (LAX → JFK)
2. Select options
3. Go to checkout
4. Use card: 4242 4242 4242 4242
5. Complete booking
6. Verify in admin panel
```

### 2. Card Declined
```
1. Follow same steps
2. Use card: 4000 0000 0000 0002
3. Should show error message
4. Booking status should remain 'pending'
```

### 3. Refund Test
```
1. Create successful booking
2. Go to admin panel
3. Find payment
4. Create refund
5. Verify refund in Stripe dashboard
```

---

## 🚀 Quick Start Testing

Right now, you can immediately test bookings:

1. **Start your app** (already running)
2. **Search for travel** (LAX → JFK working)
3. **Click "Book Now"** on a hotel or flight
4. **Enter payment details**:
   - Card: `4242 4242 4242 4242`
   - Expiry: `12/25`
   - CVC: `123`
5. **Complete booking** - No real money charged!

---

## 📚 Resources

- **Stripe Testing Guide**: https://stripe.com/docs/testing
- **Test Card Numbers**: https://stripe.com/docs/testing#cards
- **Stripe Dashboard**: https://dashboard.stripe.com/test
- **Webhook Testing**: https://stripe.com/docs/webhooks/test

---

## ❓ FAQ

**Q: Will any real money be charged?**
A: No! Your `sk_test_` keys cannot process real payments.

**Q: Can I test refunds?**
A: Yes! Create a test payment, then refund it in the admin panel or Stripe dashboard.

**Q: What happens when I go to production?**
A: Replace test keys with live keys (`sk_live_...`), and everything works the same way with real money.

**Q: Can I test 3D Secure authentication?**
A: Yes! Use card `4000 0025 0000 3155` to simulate authentication flow.

**Q: How do I know if I'm in test mode?**
A: Check your `.env` - if keys start with `sk_test_`, you're in test mode!

---

## 🎉 Summary

**You're all set!** Your application is already configured for safe testing:
- ✅ Stripe test keys installed
- ✅ No real payments possible
- ✅ Full feature testing available
- ✅ Use test cards: `4242 4242 4242 4242`

Just start booking and test away! 🚀
