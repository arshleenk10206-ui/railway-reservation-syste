from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# --- Core Data Structures ---
class Passenger:
    def __init__(self, pnr, name, age, source, destination, journey_date, train_name, seat_class, price):
        self.pnr = pnr
        self.name = name
        self.age = age
        self.source = source
        self.destination = destination
        self.journey_date = journey_date
        self.train_name = train_name
        self.seat_class = seat_class
        self.price = price
        self.status = "Confirmed"
        self.next = None

class ConfirmedLinkedList:
    def __init__(self):
        self.head = None
        self.size = 0

    def append(self, passenger):
        passenger.status = "Confirmed"
        if not self.head:
            self.head = passenger
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = passenger
        self.size += 1

    def remove(self, pnr):
        current = self.head
        prev = None
        while current:
            if current.pnr.upper() == pnr.upper():
                if prev:
                    prev.next = current.next
                else:
                    self.head = current.next
                self.size -= 1
                return current
            prev = current
            current = current.next
        return None

    def to_list(self):
        result = []
        current = self.head
        while current:
            result.append(current)
            current = current.next
        return result

class WaitingQueue:
    def __init__(self):
        self.items = []

    def enqueue(self, passenger):
        passenger.status = "Waiting"
        self.items.append(passenger)

    def dequeue(self):
        if not self.is_empty():
            passenger = self.items.pop(0)
            passenger.status = "Confirmed"
            return passenger
        return None

    def remove(self, pnr):
        for i, passenger in enumerate(self.items):
            if passenger.pnr.upper() == pnr.upper():
                return self.items.pop(i)
        return None

    def is_empty(self):
        return len(self.items) == 0

# Initialize system (Max seats set to 3 for demonstration)
MAX_SEATS = 3
confirmed_list = ConfirmedLinkedList()
waiting_queue = WaitingQueue()
pnr_counter = 1001

# Pricing chart based on class
PRICES = {
    "Sleeper (SL)": 550,
    "AC 3 Tier (3AC)": 1450,
    "AC 2 Tier (2AC)": 2100,
    "Chair Car (CC)": 950
}

# --- Web Routes ---
@app.route('/')
def index():
    confirmed_passengers = confirmed_list.to_list()
    waiting_passengers = waiting_queue.items
    
    # Calculate total revenue from confirmed bookings
    total_revenue = sum(p.price for p in confirmed_passengers)
    
    return render_template(
        'index.html',
        confirmed=confirmed_passengers,
        waiting=waiting_passengers,
        confirmed_count=confirmed_list.size,
        max_seats=MAX_SEATS,
        waiting_count=len(waiting_passengers),
        revenue=total_revenue
    )

@app.route('/book', methods=['POST'])
def book():
    global pnr_counter
    name = request.form.get('name')
    age = request.form.get('age')
    source = request.form.get('source')
    destination = request.form.get('destination')
    journey_date = request.form.get('journey_date')
    train_name = request.form.get('train_name')
    seat_class = request.form.get('seat_class')
    
    # Calculate price based on class selection
    price = PRICES.get(seat_class, 500)
    
    pnr = f"PNR{pnr_counter}"
    pnr_counter += 1
    
    passenger = Passenger(pnr, name, age, source, destination, journey_date, train_name, seat_class, price)
    
    if confirmed_list.size < MAX_SEATS:
        confirmed_list.append(passenger)
    else:
        waiting_queue.enqueue(passenger)
        
    return redirect(url_for('index'))

@app.route('/cancel', methods=['POST'])
def cancel():
    pnr = request.form.get('pnr', '').strip().upper()
    
    if not pnr:
        return redirect(url_for('index'))
    
    # 1. Try removing from confirmed linked list
    removed = confirmed_list.remove(pnr)
    if removed:
        # Automatic waiting list promotion
        if not waiting_queue.is_empty():
            promoted = waiting_queue.dequeue()
            confirmed_list.append(promoted)
    else:
        # 2. If not in confirmed, try removing from waiting queue
        waiting_queue.remove(pnr)
        
    return redirect(url_for('index'))

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)