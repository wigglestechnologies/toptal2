from django.core.mail import EmailMessage


class Observer():
    
    _observers = []
    
    def __init__(self):
        self._observers.append(self)
        self._observables = {}
    
    def observe(self, event_name, callback):
        self._observables[event_name] = callback


class Event():
    
    def __init__(self, name, data, auto_notify=True):
        self.name = name
        self.data = data
        if auto_notify:
            self.notify()
        
    def notify(self):
        for observer in Observer._observers:
            if self.name in observer._observables:
                observer._observables[self.name](self.data)

def send_mail(data):
    
    email = EmailMessage(
        from_email='no-reply@toptal-soccer.com', 
        to=(data['email_to'],), 
        subject=data['email_subject'], 
        body=data['email_body']
        )

    email.send()