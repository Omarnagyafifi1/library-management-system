# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class User(AbstractUser):
    # first_name = models.CharField(max_length=100)
    # last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)


    # Add custom fields here, if needed

    def __str__(self):
        return self.username
    

# CREATE TABLE Books (
#     book_id INTEGER PRIMARY KEY AUTOINCREMENT,
#     book_name text,
#     author text,
#     publisher text,
#     publishing_date Date,
#     category_id text,  -- foreign key from categories table
#     book_language text,
#     pages_num INTEGER check(pages_num > 0),
#     price Real check (price >=0),
#     num_of_sells INTEGER DEFAULT 0 check (num_of_sells >=0),
#     stock_quantity INTEGER DEFAULT 0 check (stock_quantity >=0),
#     evaluation INTEGER CHECK(evaluation BETWEEN 0 and 5),
#     about text,
#     cover_image text -- url of the cover image in my project.
# )

class Book (models.Model):
    book_id = models.AutoField(primary_key=True)
    book_name = models.CharField(max_length=100)
    author_name = models.CharField(max_length=50)
    publisher = models.CharField(max_length=50)
    publishing_date = models.DateField(default=timezone.now)

    category_id = models.ForeignKey('Category', on_delete=models.CASCADE)  # Assuming you have a Category model
    book_language = models.CharField(max_length=100)
    pages_num = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    num_of_sells = models.PositiveIntegerField(default=0)
    stock_quantity = models.PositiveIntegerField(default=0)
    evaluation = models.PositiveSmallIntegerField(null=True, blank=True)  # Allowing null for books without evaluation
    brief_abstraction = models.TextField(blank=True)
    long_abstraction = models.TextField(null=True)
    cover_image = models.URLField(max_length=500, blank=True)

    def __str__(self):
        return self.book_name
    

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=255, unique=True)
    category_description = models.TextField(blank=True)

    def __str__(self):
        return self.category_name
    


class Wishlist(models.Model): # we need to add some users first to add a whishlist item
    wishlist_id = models.AutoField(primary_key=True)
    
    # Equivalent of: FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    
    # Equivalent of: FOREIGN KEY (book_id) REFERENCES Books(book_id) ON DELETE CASCADE
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='wishlisted_by')
    
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.book.book_name}"
    



class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    review_text = models.TextField(blank=True)
    review_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.book.book_name} ({self.rating})"



class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    order_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.TextField()

    def update_total_price(self):
        total = sum(transaction.book.price for transaction in self.transactions.all())
        self.total_price = total
        self.save()

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"





class Transaction(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="transactions")
    user = models.ForeignKey(User,  on_delete=models.CASCADE, related_name="transactions")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="transactions")

    def __str__(self):
        return f"Transaction: {self.user.username} bought {self.book.book_name}"


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('Credit Card', 'Credit Card'),
        ('PayPal', 'PayPal'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Cash on Delivery', 'Cash on Delivery'),
    ]
    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='Pending')
    payment_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payment_method} - {self.amount} - {self.payment_status}"
    


# Signal to update total_price when a transaction is added or modified
@receiver(post_save, sender=Transaction)
def update_order_total_price_on_save(sender, instance, **kwargs):
    instance.order.update_total_price()

# Signal to update total_price when a transaction is deleted
@receiver(post_delete, sender=Transaction)
def update_order_total_price_on_delete(sender, instance, **kwargs):
    instance.order.update_total_price()




# ---------------- Notes ------------------

# -1- (related_name) is used in the reverse relation. We notice that Transaction has order attribute as a foreign
# key with related_name = 'transactions'. So I can use put transactions in the fields of Order when making the 
# OrderSerializer. If I didn't put related_name, I can use the transaction there in the form (transaction_set)

