import sys, os
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QLabel, QVBoxLayout, QScrollArea, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap
from PIL import Image
import re
import piexif
import piexif.helper

class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()

        self.setAlignment(Qt.AlignCenter)
        self.setText('\n\n Drop Image Here \n\n')
        self.setStyleSheet('''
            QLabel{
                border: 4px dashed #aaa
            }
        ''')

    def setPixmap(self, image):
        super().setPixmap(image)

class AppDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Prompt Extractor')
        self.setGeometry(200, 100, 800, 400)
        self.setAcceptDrops(True)

        main_widget = QWidget(self)
        # self.setCentralWidget(main_widget)

        mainLayout = QHBoxLayout(main_widget)

        upper_section = QVBoxLayout()
        self.photoViewer = ImageLabel()
        self.photoViewer.setMaximumSize(512,512)
        self.prompt_label = QLabel("Prompt:", self)
        self.prompt_box = QLabel(self)
        self.prompt_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.prompt_box.setWordWrap(True)
        self.pos_copy_btn=QPushButton("Copy")
        self.pos_copy_btn.setFixedSize(QSize(80,24))

        self.pos_copy_btn.clicked.connect(self.copypos)
        self.negative_label = QLabel("Negative Prompt:", self)
        self.negative_box = QLabel(self)
        self.negative_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.negative_box.setWordWrap(True)
        self.neg_copy_btn=QPushButton("Copy")
        self.neg_copy_btn.clicked.connect(self.copyneg)
        self.neg_copy_btn.setFixedSize(QSize(80,24))

        self.other_label = QLabel("Other:", self)
        self.other_data = QLabel(self)
        self.other_data.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.other_data.setWordWrap(True)

        upper_section.addWidget(self.photoViewer)

        lower_section_scroll_area = QScrollArea()
        lower_section_scroll_area.setWidgetResizable(True)
        lower_section_widget = QWidget()
        lower_section_scroll_area.setWidget(lower_section_widget)
        lower_section_layout = QVBoxLayout(lower_section_widget)
        lower_section_layout.addWidget(self.prompt_label)
        lower_section_layout.addWidget(self.prompt_box)
        lower_section_layout.addWidget(self.pos_copy_btn)
        lower_section_layout.addWidget(self.negative_label)
        lower_section_layout.addWidget(self.negative_box)
        lower_section_layout.addWidget(self.neg_copy_btn)
        lower_section_layout.addWidget(self.other_label)
        lower_section_layout.addWidget(self.other_data)

        mainLayout.addLayout(upper_section)
        mainLayout.addWidget(lower_section_scroll_area)

        self.setLayout(mainLayout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasImage:
            event.setDropAction(Qt.CopyAction)
            file_path = event.mimeData().urls()[0].toLocalFile()
            self.set_image(file_path)
            prompt_string = self.parse_image(file_path)
            # QMessageBox.question(self, "Image Data", prompt_string , QMessageBox.Ok, QMessageBox.Ok)
            event.accept()
        else:
            event.ignore()

    def set_image(self, file_path):
        pixmap = QPixmap(file_path)
        pixmap = pixmap.scaledToWidth(self.photoViewer.maximumWidth()) if pixmap.width() > pixmap.height() else pixmap.scaledToHeight(self.photoViewer.maximumHeight())

        self.photoViewer.setPixmap(pixmap)

    def parse_image(self, filename):
        with open(filename,'rb') as file:
            img = Image.open(file)
        extension = filename.split('.')[-1]
        parameters = ""
        comfy = False
        if extension.lower() == 'png':
            try:
                parameters = img.info['parameters']
                parameters = "Prompt: " + parameters
            except:
                try:
                    parameters = str(img.info['comment'])
                    comfy = True
                except:
                    return "Error loading prompt info."
        elif extension.lower() in ("jpg", "jpeg", "webp"):
            try:
                exif = piexif.load(img.info["exif"])
                parameters = (exif or {}).get("Exif", {}).get(piexif.ExifIFD.UserComment, b'')
                parameters = piexif.helper.UserComment.load(parameters)
                parameters = "Prompt: " + parameters
            except:
                try:
                    parameters = str(img.info['comment'])
                    comfy = True
                except:
                    print("Error loading prompt info")
                    return "Error loading prompt info."
        if(comfy):
            parameters = parameters.replace('\\n',' ')
        else:
            parameters = parameters.replace('\n',' ')


        patterns = [
            "Positive Prompt: ",
            "Prompt: ",
            "Negative prompt: ",
            "Negative Prompt: ",
            "Steps: ",
            "Sampler: ",
            "CFG scale: ",
            "Seed: ",
            "Size: ",
            "Model: ",
            "Model hash: ",
            "Denoising strength: ",
            "Version: ",
            "ControlNet 0",
            "Controlnet 1",
            "Batch size: ",
            "Batch pos: ",
            "Hires upscale: ",
            "Hires steps: ",
            "Hires upscaler: ",
            "Template: ",
            "Negative Template: ",
            "Seed: "
        ]
        if(comfy):
            parameters = parameters[2:]
            parameters = parameters[:-1]

        keys = re.findall("|".join(patterns), parameters)
        values = re.split("|".join(patterns), parameters)
        values = [x for x in values if x]
        results = {}
        result_string = ""

        for item in range(len(keys)):
            # print(keys[item],values[item].rstrip(', '))
            if(keys[item] != "Prompt: " and keys[item] != "Positive Prompt: "  and keys[item] != "Negative prompt: " and keys[item] != "Negative Prompt: " and keys[item] != "Template: "  and keys[item] != "Negative Template: "):
                result_string += keys[item] + values[item].rstrip(', ')
                result_string += "\n"
            results[keys[item].replace(": ","")] = values[item].rstrip(', ')
        #print(results.keys())
        
        if(comfy):
            #print("fixing key")
            results['Prompt'] = results['Positive Prompt']
            results['Negative prompt'] = results['Negative Prompt']

        self.prompt_box.setText(results['Prompt'])
        self.negative_box.setText(results['Negative prompt'])
        self.other_data.setText(result_string)
        return result_string

    def copypos(self):
        clipboard.setText(self.prompt_box.text())
        
    def copyneg(self):
        clipboard.setText(self.negative_box.text())

    
app = QApplication(sys.argv)
clipboard = app.clipboard()
demo = AppDemo()
demo.show()
sys.exit(app.exec_())
