import os
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

    def to_dict(self):
        return {
            "pnr": self.pnr,
            "name": self.name,
            "age": self.age,
            "source": self.source,
            "destination": self.destination,
            "journey_date": self.journey_date,
            "train_name": self.train_name,
            "seat_class": self.seat_class,
            "price": self.price,
            "status": self.status
        }

class ConfirmedLinkedList:
    def __init__(self, capacity=4):
        self.head = None
        self.size = 0
        self.capacity = capacity

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
            if current.pnr == pnr:
                if prev:
                    prev.next = current.next
                else:
                    self.head = current.next
                self.size -= 1
                return current
            prev = current
            current = current.next
        return None

    def is_full(self):
        return self.size >= self.capacity

    def get_all(self):
        result = []
        current = self.head
        while current:
            result.append(current)
            current = current.next
        return result

class WaitingQueue:
    def __init__(self):
        self.queue = []

    def enqueue(self, passenger):
        passenger.status = "Waiting"
        self.queue.append(passenger)

    def dequeue(self):
        if self.queue:
            return self.queue.pop(0)
        return None

    def remove(self, pnr):
        for i, passenger in enumerate(self.queue):
            if passenger.pnr == pnr:
                return self.queue.pop(i)
        return None

    def is_empty(self):
        return len(self.queue) == 0

    def get_all(self):
        return self.queue

# --- Global State ---
confirmed_list = ConfirmedLinkedList(capacity=4)
waiting_queue = WaitingQueue()
pnr_counter = 1001

TRAINS = {
    "Rajdhani Express": {
        "route": "New Delhi → Mumbai",
        "months": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # All year
        "fares": {"3AC": 2650, "2AC": 3600, "1AC": 4700}
    },
    "Shatabdi Express": {
        "route": "New Delhi → Amritsar",
        "months": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "fares": {"CC": 1150, "EC": 2300}
    },
    "Duronto Express": {
        "route": "Howrah → Chennai",
        "months": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "fares": {"SL": 780, "3AC": 1980, "2AC": 2850}
    },
    "Himalayan Summer Special": {
        "route": "Delhi → Shimla (Apr-Jun)",
        "months": [0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0],
        "fares": {"CC": 890, "EC": 1750}
    },
    "Monsoon Konkan Special": {
        "route": "Mumbai → Goa (Jun-Sep)",
        "months": [0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
        "fares": {"SL": 620, "3AC": 1640}
    },
    "Winter Pilgrim Special": {
        "route": "Varanasi → Haridwar (Nov-Feb)",
        "months": [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
        "fares": {"SL": 540, "3AC": 1420, "2AC": 2100}
    }
}

@app.route('/')
def index():
    confirmed = confirmed_list.get_all()
    waiting = waiting_queue.get_all()
    total_collections = sum(p.price for p in confirmed) + sum(p.price for p in waiting)
    
    # Calculate seat slots
    slots = []
    curr = confirmed_list.head
    for i in range(confirmed_list.capacity):
        if curr:
            slots.append(curr)
            curr = curr.next
        else:
            slots.append(None)
            
    return render_template(
        'index.html',
        confirmed=confirmed,
        waiting=waiting,
        slots=slots,
        total_collections=total_collections,
        trains=TRAINS,
        capacity=confirmed_list.capacity
    )

@app.route('/book', methods=['POST'])
def book():
    global pnr_counter
    name = request.form.get('name')
    age = int(request.form.get('age', 25))
    source = request.form.get('source')
    destination = request.form.get('destination')
    journey_date = request.form.get('journey_date')
    train_name = request.form.get('train_name')
    seat_class = request.form.get('seat_class')
    
    # Pricing logic
    train_info = TRAINS.get(train_name, {})
    price = train_info.get("fares", {}).get(seat_class, 1000)
    
    pnr = f"PNR{pnr_counter}"
    pnr_counter += 1
    
    passenger = Passenger(pnr, name, age, source, destination, journey_date, train_name, seat_class, price)
    
    if not confirmed_list.is_full():
        confirmed_list.append(passenger)
    else:
        waiting_queue.enqueue(passenger)
        
    return redirect(url_for('index'))

@app.route('/cancel', methods=['POST'])
def cancel():
    pnr = request.form.get('pnr', '').strip().upper()
    if not pnr:
        return redirect(url_for('index'))

    removed = confirmed_list.remove(pnr)
    if removed:
        if not waiting_queue.is_empty():
            promoted = waiting_queue.dequeue()
            confirmed_list.append(promoted)
    else:
        waiting_queue.remove(pnr)

    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset():
    global confirmed_list, waiting_queue, pnr_counter
    confirmed_list = ConfirmedLinkedList(capacity=4)
    waiting_queue = WaitingQueue()
    pnr_counter = 1001
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)