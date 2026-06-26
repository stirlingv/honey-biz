# 🐝 Bear Creek Apiaries - Admin Guide

## How to Manage Your Business

This guide will help you use the admin panel to manage orders, requests, and inventory.

---

## 📱 Getting Started

### Logging In

1. Go to: `https://your-website.com/admin/` (or `http://127.0.0.1:8000/admin/` when testing locally)
1. Enter your username and password
1. Click "Log in"

You'll see the main dashboard with all the different sections you can manage.

---

## 📬 When You Get a Text/Email Notification

When a customer submits a request, you'll receive:

- **Text message (SMS)**: Quick alert with the key details
- **Email**: Full details you can reference

The text will tell you if the customer **wants a callback** (📞 CALLBACK) - these customers prefer a phone call!

---

## 🍯 Managing Honey Orders

### Viewing Orders

1. Click **"Orders"** on the main page
1. You'll see a list of all orders with:
   - Order number (#1, #2, etc.)
   - Customer name and contact info
   - What they ordered
   - Total price
   - Status (colored badge)
   - If they want a callback (📞 CALL)

### Order Status Meanings

| Status | Color | What It Means |
|--------|-------|---------------|
| PENDING | Yellow | New order - needs attention |
| PROCESSING | Purple | You're working on it |
| COMPLETED | Green | Done! Order fulfilled |
| CANCELLED | Red | Customer cancelled |

### Updating an Order Status

**Quick way (from the list):**

1. Click the dropdown next to the status
1. Select the new status
1. Click **"Save"** at the bottom

**Or update multiple at once:**

1. Check the boxes next to orders you want to update
1. Select an action from the dropdown (e.g., "✅ Mark as COMPLETED")
1. Click **"Go"**

### Viewing Full Order Details

1. Click the order number (e.g., "#5")
1. You'll see all customer info, address, notes, etc.
1. Click **"Save"** after making any changes

### ✅ Acknowledge Orders (Required)

Acknowledging an order means you took an action (like changing the status or payment status).
This keeps you organized and stops reminders.

**How to acknowledge:**

1. Open the order
1. Change **Status** or **Payment Status** (this is required)
1. Click the **"Acknowledge Order"** button at the top

If you try to acknowledge without taking any action, the system will warn you.

### ✅ Bulk Acknowledge (Multiple Orders)

1. Check the boxes next to orders you already acted on
1. From the **Actions** dropdown, choose **"Acknowledge selected orders"**
1. Click **Go**

Orders without any action will be skipped and you will see a warning.

### ⏰ Reminder Rules

- **First reminder**: 24 hours after a new order if it is still **PENDING** and **UNPAID**
- **Second reminder**: 24 hours after you acknowledge if the order is still **PENDING** and **UNPAID**
- As soon as you update status or payment status, reminders stop

### 🗂 Viewing Archived Orders (30+ Days Old)

Completed orders older than 30 days are hidden from the default list.
To view them:

1. Open the Orders list
1. Use the **Order age** filter on the right
1. Choose **"Archived (completed 30+ days ago)"**

### Suggested Workflow (Best Practices)

1. Open new order
1. Update **Status** to **PROCESSING** or **AWAITING_PAYMENT**
1. Click **Acknowledge Order**
1. Fulfill the order and set **Status** to **COMPLETED**

---

## 🐝 Managing Nuc Requests

### Viewing Requests

1. Click **"Nuc Requests"** on the main page
1. Each request shows:
   - Request number (NUC-1, NUC-2, etc.)
   - Customer info
   - How many nucs they want
   - Their experience level
   - Preferred pickup date

### Request Status Workflow

1. **PENDING** → New request, call/email the customer
1. **CONTACTED** → You've reached out to them
1. **COMPLETED** → They picked up their nucs!
1. **DECLINED** → They cancelled or you couldn't fulfill

### Adding Your Notes

1. Click on the request to open it
1. Scroll to **"Status & Notes"**
1. Add notes in the **"Admin notes"** field (e.g., "Called 1/2, will pick up Saturday")
1. Click **"Save"**

---

## 🌻 Managing Pollination Requests

### Viewing Requests

1. Click **"Pollination Requests"** on the main page
1. Shows: customer, crop type, acreage, start date, your quote

### Adding a Price Quote

1. Click the request to open it
1. Find **"Quoted price"** field
1. Enter your price (just the number, e.g., `500.00`)
1. Update status to **"Contacted"**
1. Click **"Save"**

### Status Workflow

1. **PENDING** → New request
1. **CONTACTED** → You've sent a quote
1. **SCHEDULED** → They accepted, bees are scheduled
1. **COMPLETED** → Service finished

---

## 🏠 Managing Bee Removal Requests

### ⚠️ Important: Check Urgency First!

Bee removal requests are sorted by urgency:

- 🟢 **LOW** - No rush
- 🟡 **MEDIUM** - Would like it soon
- 🟠 **HIGH** - Causing problems
- 🔴 **EMERGENCY** - Safety concern (respond ASAP!)

### Check If Sprayed

Look for **"⚠️SPRAYED"** in the location column - this means someone sprayed pesticides on the bees. Important to know before removal!

### Adding a Quote & Scheduling

1. Click the request to open it
1. Enter your **"Quoted price"**
1. Set the **"Scheduled date"** when you plan to do the removal
1. Update status to **"Scheduled"**
1. Click **"Save"**

---

## 📞 Managing Callback Requests

These are simple "please call me" requests from the footer.

### Viewing Callbacks

1. Click **"Callback Requests"**
1. See: name, phone, what they're interested in, best time to call

### What They're Interested In

The colored badge shows what they want to discuss:

- 🟠 **Honey** - Honey products
- 🟢 **Nucs** - Bee starter colonies
- 🟣 **Pollination** - Pollination services
- 🔴 **Bee Removal** - Bee removal
- 🔵 **General** - Just a question

### After You Call

1. Open the callback request
1. Add notes about what you discussed
1. Change status to **"Contacted"** or **"Completed"**
1. Click **"Save"**

---

## 📦 Managing Products (Inventory)

### Viewing Products

1. Click **"Products"** on the main page
1. See all your honey products with prices and stock status

### Marking Products Out of Stock

**Quick way:**

1. Uncheck the **"In stock"** checkbox in the list
1. Click **"Save"**

**Multiple products:**

1. Check boxes next to products
1. Select **"❌ Mark as OUT OF STOCK"**
1. Click **"Go"**

### Adding a New Product

1. Click **"Add Product"** (top right)
1. Fill in:
   - Name (e.g., "Wildflower Honey")
   - Size — the jar volume (e.g., "Pint", "Quart")
   - Description
   - Price
   - Check **"In stock"** if available
1. Click **"Save"**

### Editing a Product

1. Click the product name
1. Make your changes
1. Click **"Save"**

---

## 🔍 Finding Things

### Search

Every page has a search box at the top. Type a name, email, or phone number to find orders/requests.

### Filter

Use the filters on the right side to narrow down:

- By status (Pending, Completed, etc.)
- By date
- By product or crop type

### Date Navigation

The calendar bar at the top lets you jump to specific months.

---

## 💡 Quick Tips

1. **Look for 📞 CALL** - These customers want a phone call!
2. **Check urgency colors** - Red = urgent, respond quickly
3. **Add admin notes** - Keep track of your conversations
4. **Use bulk actions** - Check multiple boxes + action dropdown to update many at once
5. **Save often** - Always click "Save" after making changes

---

## ❓ Need Help?

If something isn't working, contact your website administrator (Stirling).

---

*Last updated: January 2026*
