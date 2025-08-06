from django.db import models

class ATM_Card(models.Model):
    atmcard_num = models.CharField(max_length=16, primary_key=True)
    atmcard_pin = models.CharField(max_length=4)
    cardholder_name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    email = models.EmailField() 
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.cardholder_name} - {self.atmcard_num}"


    class Meta:
        app_label = 'money'
    

class Transaction(models.Model):
    card = models.ForeignKey(ATM_Card, on_delete=models.CASCADE)
    txn_type = models.CharField(max_length=10, choices=[('Withdraw', 'Withdraw'), ('Deposit', 'Deposit')])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)