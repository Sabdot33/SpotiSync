import logging
from PyQt5.QtWidgets import QWidget, QMessageBox, QInputDialog

# Popup Dialog Boxes
def show_error_message(msg_type, error_message):
    """
    Displays a message box with the specified type and error message.
    Args:
        msg_type (str): The type of message box to display. Can be "critical", "information", or "question".
        error_message (str): The message to display in the message box.

    Returns:
        None
        bool: True if the user clicked the "Yes" button, False if the user clicked the "No" button.

    Raises:
        ValueError: If the specified type is not "critical", "information", or "question".
    """

    if msg_type == "critical":
        QMessageBox.critical(QWidget(), "Error", error_message)
        return None

    elif msg_type == "information":
        QMessageBox.information(QWidget(), "Info", error_message)
        return None

    elif msg_type == "question":
        reply = QMessageBox.question(QWidget(), "Question", error_message, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            return True
        else:
            return False

    else:
        raise ValueError("Invalid message box msg_type")

def enter_value_and_return(message):
    input_field, ok = QInputDialog.getText(QWidget(), "Enter new value:", message)
    if ok:
        logging.debug(str(input_field))
        return str(input_field)
    else:
        logging.debug("User cancelled input")
        return None