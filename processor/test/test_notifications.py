import processor.notifications as notifications


def test_send_email():
    notifications.send_email(["r.bhargava@northeastern.edu"], "Feminicide MC Story Processor Test", "Is this working?")


if __name__ == "__main__":
    test_send_email()
