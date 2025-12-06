"""
QuickBooks Integration Service

Handles OAuth authentication and payment processing with QuickBooks.
"""

import logging
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.urls import reverse

from intuitlib.client import AuthClient
from intuitlib.enums import Scopes

logger = logging.getLogger(__name__)


class QuickBooksService:
    """Service class for QuickBooks integration"""
    
    def __init__(self):
        self.client_id = settings.QUICKBOOKS_CLIENT_ID
        self.client_secret = settings.QUICKBOOKS_CLIENT_SECRET
        self.redirect_uri = settings.QUICKBOOKS_REDIRECT_URI
        self.environment = settings.QUICKBOOKS_ENVIRONMENT
        self.company_id = settings.QUICKBOOKS_COMPANY_ID
        
        # Initialize OAuth client
        self.auth_client = AuthClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            environment=self.environment,
        )
    
    def get_authorization_url(self, state=None):
        """
        Generate the QuickBooks OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL string
        """
        scopes = [
            Scopes.ACCOUNTING,
            Scopes.PAYMENT,
        ]
        
        auth_url = self.auth_client.get_authorization_url(scopes, state_token=state)
        return auth_url
    
    def handle_callback(self, auth_code, realm_id):
        """
        Handle the OAuth callback and exchange code for tokens.
        
        Args:
            auth_code: Authorization code from QuickBooks
            realm_id: The QuickBooks company ID (realm)
            
        Returns:
            dict with access_token, refresh_token, and realm_id
        """
        try:
            self.auth_client.get_bearer_token(auth_code, realm_id=realm_id)
            
            return {
                'access_token': self.auth_client.access_token,
                'refresh_token': self.auth_client.refresh_token,
                'realm_id': realm_id,
                'expires_in': self.auth_client.expires_in,
            }
        except Exception as e:
            logger.error(f"Error exchanging auth code: {e}")
            raise
    
    def refresh_access_token(self, refresh_token):
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            dict with new access_token and refresh_token
        """
        try:
            self.auth_client.refresh(refresh_token=refresh_token)
            
            return {
                'access_token': self.auth_client.access_token,
                'refresh_token': self.auth_client.refresh_token,
                'expires_in': self.auth_client.expires_in,
            }
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise
    
    def create_invoice(self, order, access_token, realm_id):
        """
        Create an invoice in QuickBooks for an order.
        
        Args:
            order: Order model instance
            access_token: Valid QuickBooks access token
            realm_id: QuickBooks company ID
            
        Returns:
            dict with invoice details including payment link
        """
        from quickbooks import QuickBooks
        from quickbooks.objects.invoice import Invoice
        from quickbooks.objects.customer import Customer
        from quickbooks.objects.detailline import SalesItemLine, SalesItemLineDetail
        from quickbooks.objects.item import Item
        
        try:
            # Initialize QuickBooks client
            client = QuickBooks(
                auth_client=self.auth_client,
                refresh_token=access_token,
                company_id=realm_id,
            )
            
            # Find or create customer
            customer = self._find_or_create_customer(client, order)
            
            # Find or create item (product)
            item = self._find_or_create_item(client, order.product)
            
            # Create invoice
            invoice = Invoice()
            invoice.CustomerRef = customer.to_ref()
            
            # Add line item
            line = SalesItemLine()
            line.Amount = float(order.total_price)
            line.Description = f"{order.product.name} - {order.product.size}"
            
            line_detail = SalesItemLineDetail()
            line_detail.ItemRef = item.to_ref()
            line_detail.Qty = order.quantity
            line_detail.UnitPrice = float(order.product.price)
            
            line.SalesItemLineDetail = line_detail
            invoice.Line = [line]
            
            # Add customer email for invoice delivery
            invoice.BillEmail = {"Address": order.email}
            invoice.EmailStatus = "NeedToSend"
            
            # Save invoice
            invoice.save(qb=client)
            
            logger.info(f"Created QuickBooks invoice {invoice.Id} for order {order.id}")
            
            return {
                'invoice_id': invoice.Id,
                'invoice_number': invoice.DocNumber,
                'total': invoice.TotalAmt,
            }
            
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            raise
    
    def _find_or_create_customer(self, client, order):
        """Find existing customer or create new one"""
        from quickbooks.objects.customer import Customer
        
        # Search for existing customer by email
        customers = Customer.filter(
            PrimaryEmailAddr=order.email,
            qb=client
        )
        
        if customers:
            return customers[0]
        
        # Create new customer
        customer = Customer()
        customer.DisplayName = f"{order.first_name} {order.last_name}"
        customer.GivenName = order.first_name
        customer.FamilyName = order.last_name
        customer.PrimaryEmailAddr = {"Address": order.email}
        customer.PrimaryPhone = {"FreeFormNumber": order.phone}
        customer.BillAddr = {
            "Line1": order.address,
            "City": order.city,
            "CountrySubDivisionCode": order.state,
            "PostalCode": order.zip_code,
        }
        
        customer.save(qb=client)
        return customer
    
    def _find_or_create_item(self, client, product):
        """Find existing item or create new one"""
        from quickbooks.objects.item import Item
        from quickbooks.objects.account import Account
        
        # Search for existing item by name
        items = Item.filter(
            Name=product.name[:100],  # QB has 100 char limit
            qb=client
        )
        
        if items:
            return items[0]
        
        # Get income account (required for item creation)
        accounts = Account.filter(AccountType="Income", qb=client)
        if not accounts:
            raise Exception("No income account found in QuickBooks")
        
        income_account = accounts[0]
        
        # Create new item
        item = Item()
        item.Name = product.name[:100]
        item.Description = product.description[:4000] if product.description else ""
        item.Type = "Service"  # or "Inventory" if tracking inventory
        item.UnitPrice = float(product.price)
        item.IncomeAccountRef = income_account.to_ref()
        
        item.save(qb=client)
        return item
    
    def get_payment_link(self, invoice_id, access_token, realm_id):
        """
        Get a payment link for an invoice.
        
        Note: QuickBooks Payments creates payment links automatically
        when invoices are emailed. This method retrieves the link.
        
        Args:
            invoice_id: QuickBooks invoice ID
            access_token: Valid access token
            realm_id: QuickBooks company ID
            
        Returns:
            Payment URL string or None
        """
        from quickbooks import QuickBooks
        from quickbooks.objects.invoice import Invoice
        
        try:
            client = QuickBooks(
                auth_client=self.auth_client,
                refresh_token=access_token,
                company_id=realm_id,
            )
            
            invoice = Invoice.get(invoice_id, qb=client)
            
            # The invoice link that customers can use to pay
            # Format: https://app.qbo.intuit.com/app/customerlink?...
            if hasattr(invoice, 'InvoiceLink'):
                return invoice.InvoiceLink
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting payment link: {e}")
            return None
    
    def check_payment_status(self, invoice_id, access_token, realm_id):
        """
        Check if an invoice has been paid.
        
        Args:
            invoice_id: QuickBooks invoice ID
            access_token: Valid access token
            realm_id: QuickBooks company ID
            
        Returns:
            dict with payment status information
        """
        from quickbooks import QuickBooks
        from quickbooks.objects.invoice import Invoice
        
        try:
            client = QuickBooks(
                auth_client=self.auth_client,
                refresh_token=access_token,
                company_id=realm_id,
            )
            
            invoice = Invoice.get(invoice_id, qb=client)
            
            balance = Decimal(str(invoice.Balance))
            total = Decimal(str(invoice.TotalAmt))
            
            if balance == 0:
                status = 'paid'
            elif balance < total:
                status = 'partial'
            else:
                status = 'unpaid'
            
            return {
                'status': status,
                'balance': balance,
                'total': total,
                'paid_amount': total - balance,
            }
            
        except Exception as e:
            logger.error(f"Error checking payment status: {e}")
            raise


# Singleton instance
quickbooks_service = QuickBooksService()
