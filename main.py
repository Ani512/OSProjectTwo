from threading import Semaphore, Thread, Lock
from queue import Queue, Empty
import random
import time

maxCustomers = 50

# the list stores the state of the teller -> (false if free)
totalTellers = [False, False, False]

# ONLY TWO Tellers are allowed inside the safe
safeSemaphore = Semaphore(2)

# ONLY 1 MANAGER
managerSemaphore = Semaphore(1)

tellerSemaphore = Semaphore(3)

printLock = Lock()


class Teller:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"{self.name}"


class Customer:
    def __init__(self, name):
        self.transactionType = None
        self.name = name

    def setTransactionType(self, transaction):
        self.transactionType = transaction

    def getTransactionType(self):
        return f"{self.transactionType}"

    def __str__(self):
        return f"{self.name}"

# Lock helps prevent different threads writing at the same time
def printUsingLock(msg):
    printLock.acquire()
    try:
        print(msg)
    finally:
        printLock.release()


def customerRun(customer, tellerQueue):
    depositOrWithdraw = random.choice([0, 1])  # gives type of transaction
    transactionType = ''

    if depositOrWithdraw == 0:
        transactionType = 'deposit'
        printUsingLock(f"{customer} wants to DEPOSIT")

    else:
        transactionType = 'withdraw'
        printUsingLock(f"{customer} wants to WITHDRAW")
    customer.setTransactionType(transactionType)
    # customer takes some time to go to the bank
    time.sleep(random.uniform(0.05, 0.1))
    printUsingLock(f"{customer} is going to the bank")
    try:
        printUsingLock(f"{customer} is getting in line")
        try:
            tellerSemaphore.acquire()
        except:
            print("Error while acquiring teller thread")
        printUsingLock(f"{customer} is selecting a teller")

# the False check lets me know if a teller is busy or not
        if totalTellers[0] == False:
            totalTellers[0] = customer
            printUsingLock(f"{customer} goes to Teller 1")
        elif totalTellers[1] == False:
            totalTellers[1] = customer
            printUsingLock(f"{customer} goes to Teller 2")
        elif totalTellers[2] == False:
            totalTellers[2] = customer
            printUsingLock(f"{customer} goes to Teller 3")

        tellerQueue.put(customer)
    except Exception as Error:
        print("Code Broken. Stacktrace - " + str(Error))


def tellerRun(teller, tellerQueue):
    currentTeller = teller.name
    printUsingLock(f"{currentTeller} is ready to serve")

    currentTellerNumber = int(currentTeller[7])
    while True:
        try:
            printUsingLock(f"{currentTeller} is waiting for a customer")
            # Going to the safe, waiting for it if it is occupied by two tellers
            customer = tellerQueue.get(timeout=2)
            printUsingLock(f"{customer} introduces itself to {currentTeller}")
            printUsingLock(f"{currentTeller} is serving {customer}")
            printUsingLock(
                f"{customer} asks for a {customer.getTransactionType()} transaction")
            printUsingLock(
                f"{currentTeller} is handling the {customer.getTransactionType()} transaction")

            if customer.transactionType == 'withdraw':
                printUsingLock(f"{currentTeller} is going to the manager")
                try:
                    managerSemaphore.acquire()
                except:
                    print("Error while going to Manager")
                printUsingLock(
                    f"{currentTeller} is getting the manager's permission")
                # the teller thread should block for a random duration from 5 to 30 ms
                time.sleep(random.uniform(0.005, 0.03))
                printUsingLock(
                    f"{currentTeller} has got the manager's permission")
                managerSemaphore.release()

            printUsingLock(f"{currentTeller} is going to the safe")
            try:
                safeSemaphore.acquire()
            except:
                print("Error while going to safe")
            printUsingLock(f"{currentTeller} is in the safe")
            # the teller will physically perform the transaction by blocking for a random duration of between 10 and 50 ms
            time.sleep(random.uniform(0.01, 0.05))
            printUsingLock(f"{currentTeller} is leaving the safe")
            safeSemaphore.release()
            printUsingLock(
                f"{currentTeller} finishes {customer}'s {customer.getTransactionType()} transaction")
            printUsingLock(f"{customer} thanks {currentTeller} and leaves")
            totalTellers[currentTellerNumber-1] = False
            tellerSemaphore.release()

        except Empty:
            printUsingLock(f"{currentTeller} is leaving for the day")
            break


if __name__ == '__main__':
    tellerQueue = Queue()

# creating 3 new tellers
    tellers = []
    for tel in range(1, len(totalTellers)+1):
        tellers.append(Teller("Teller " + str(tel)))

# creating threads for the tellers
    tellerThreadList = []
    for teller in range(0, len(tellers)):
        tellerThreadList.append(Thread(
            name="tellerThread"+str(teller), target=tellerRun, args=(tellers[teller], tellerQueue)))

# starting the threads
    for telThread in tellerThreadList:
        telThread.start()

# creating 50 customers
    customers = []
    for customer in range(1, maxCustomers + 1):
        customers.append(Customer("Customer " + str(customer)))

# creating threads for the 50 customers
    customerThreadList = []
    for customer in range(0, len(customers)):
        customerThreadList.append(Thread(name="customerThread"+str(customer),
                                  target=customerRun, args=(customers[customer], tellerQueue)))

# starting the customer threads
    for custThread in customerThreadList:
        custThread.start()

    printUsingLock("Bank is closing for the day")
