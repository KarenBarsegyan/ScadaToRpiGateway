# file_browser_ui.py
  
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
  
import sys
  
# A simple widget consisting of a QLabel, a QLineEdit and a 
# QPushButton. The class could be implemented in a separate 
# script called, say, file_browser.py
class FileBrowser(QWidget): 
    def __init__(self, title):
        QWidget.__init__(self)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.filter_name = 'All files (*.*)'
        self.dirpath = QDir.currentPath()
        self.filepath = ''
        
        self.label = QLabel()
        self.label.setText(title)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.label)
        
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setMinimumWidth(500)
        
        layout.addWidget(self.lineEdit)
        
        self.button = QPushButton('Search')
        self.button.clicked.connect(self.getFile)
        layout.addWidget(self.button)
       

    # For example, 
    #    setFileFilter('Images (*.png *.xpm *.jpg)')
    def setFileFilter(self, text):
        self.filter_name = text        
    def setDefaultDir(self, path):
        self.dirpath = path

    def setCallBack(self, func):
        self._CallbackFunc = func

    def getFile(self):     
        filepath = QFileDialog.getExistingDirectory(self, caption='Choose Directory',
                                                    directory=self.dirpath,
                                                    options = QFileDialog.ReadOnly)
        self.setPath(filepath)
        self._CallbackFunc()

    def getPath(self):
        return self.filepath
    
    def setPath(self, filepath: str):
        self.filepath = filepath.replace(self.dirpath, '')
        self.lineEdit.setText(self.filepath)  

  
  
class Demo(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        
        # Ensure our window stays in front and give it a title
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowTitle("File Browsing Dialog")
        self.setFixedSize(400, 300)
        
        # Create and assign the main (vertical) layout.
        vlayout = QVBoxLayout()
        self.setLayout(vlayout)    
        
        self.fileBrowserPanel(vlayout)
        vlayout.addStretch()
        self.addButtonPanel(vlayout)
        self.show()
    #--------------------------------------------------------------------
    def fileBrowserPanel(self, parentLayout):
        vlayout = QVBoxLayout()
    	
        self.fileFB = FileBrowser('Open File', FileBrowser.OpenFile)
        self.filesFB = FileBrowser('Open Files', FileBrowser.OpenFiles)
        self.dirFB = FileBrowser('Open Dir', FileBrowser.OpenDirectory)
        self.saveFB = FileBrowser('Save File', FileBrowser.SaveFile)
        
        vlayout.addWidget(self.fileFB)
        vlayout.addWidget(self.filesFB)
        vlayout.addWidget(self.dirFB)
        vlayout.addWidget(self.saveFB)
        
        vlayout.addStretch()
        parentLayout.addLayout(vlayout)
    #--------------------------------------------------------------------
    def addButtonPanel(self, parentLayout):
        hlayout = QHBoxLayout()
        hlayout.addStretch()
        
        self.button = QPushButton("OK")
        self.button.clicked.connect(self.buttonAction)
        hlayout.addWidget(self.button)
        parentLayout.addLayout(hlayout)
    #--------------------------------------------------------------------
    def buttonAction(self):
        print(self.fileFB.getPaths())
        print(self.filesFB.getPaths())
        print(self.dirFB.getPaths())
        print(self.saveFB.getPaths())
        
    #--------------------------------------------------------------------
  
# ========================================================                
if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    demo = Demo() # <<-- Create an instance
    demo.show()
    sys.exit(app.exec_())