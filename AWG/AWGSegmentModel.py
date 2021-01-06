"""
Created on 09 Dec 2015 at 8:38 PM

author: jmizrahi
"""
from PyQt5 import QtCore, QtWidgets, QtGui

from modules.Expression import Expression
from modules.firstNotNone import firstNotNone
from modules.enum import enum
from modules.MagnitudeParser import isIdentifier, isValueExpression
from uiModules.KeyboardFilter import KeyListFilter
import logging

nodeTypes = enum('segmentSet', 'segment')

class AWGSegmentNode(object):
    def __init__(self, parent, *args, **kwds):
        self.parent = parent
        self.children = []
        self.enabled = kwds.get('enabled', True)
        self.name = ""
        self.position = None

    def childCount(self):
        return len(self.children)

    def child(self, row):
        if 0 <= row < self.childCount():
            return self.children[row]

    def name(self):
        return self.name

    def position(self):
        return self.position

    @property
    def row(self):
        """Return this node's row in its parent's list of children"""
        return self.parent.children.index(self) if (self.parent and self.parent.children) else 0

    @row.setter
    def row(self, newRow):
        if 0 <= newRow < len(self.parent.children):
            self.parent.children.insert( newRow, self.parent.children.pop(self.row) )

    def __getstate__(self):
        dictcopy = dict(self.__dict__)
        dictcopy.pop('expression', None)
        dictcopy.pop('stack', None)
        return dictcopy


class AWGSegmentSet(AWGSegmentNode):
    def __init__(self, parent, *args, **kwds):
        super(AWGSegmentSet, self).__init__(parent)
        self.nodeType = nodeTypes.segmentSet
        self.repetitions = kwds.get('repetitions', 'R0')

class AWGSegment(AWGSegmentNode):
    expression = Expression()
    def __init__(self, parent, *args, **kwds):
        super(AWGSegment, self).__init__(parent)
        self.nodeType = nodeTypes.segment
        self.stack = None
        self.equation = kwds.get('equation', 'V0')
        self.duration = kwds.get('duration', 'T0')

    def __setstate__(self, state):
        self.__dict__ = state
        #self.__dict__['expression'] = Expression()
        self.__dict__['stack'] = None


class AWGSegmentModel(QtCore.QAbstractItemModel):
    """Model for displaying AWG segments when the AWGUi is in segment mode"""
    segmentChanged = QtCore.pyqtSignal()
    positionChanged = QtCore.pyqtSignal()
    def __init__(self, channel, settings, globalDict, parent=None):
        super(AWGSegmentModel, self).__init__(parent)
        self.channel = channel
        self.settings = settings
        self.globalDict = globalDict
        self.root = self.settings.channelSettingsList[self.channel]['segmentDataRoot']
        self.columnNames = ['position', 'enabled', 'name', 'equation', 'duration', 'repetitions']
        self.numColumns = len(self.columnNames)
        self.column = enum(*self.columnNames)
        self.allowDeletion=True
        # self.segmentSetBG = QtGui.QColor(255, 253, 222, 255)
        self.colorDict = {}
        self.colorList = [QtGui.QColor(255, 51, 51, 100),
                          QtGui.QColor(255, 153, 51, 100),
                          QtGui.QColor(255, 255, 51, 100),
                          QtGui.QColor(51, 255, 153, 100),
                          QtGui.QColor(51, 255, 255, 100),
                          QtGui.QColor(51, 153, 255, 100),
                          QtGui.QColor(51, 51, 255, 100),
                          QtGui.QColor(153, 51, 255, 100),
                          QtGui.QColor(255, 51, 255, 100),
                          QtGui.QColor(255, 51, 153, 100)]
        self.incrementor = 0
        self.headerLookup = {
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.position): "Position",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.enabled): "Enabled",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.name): "Name",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.equation): "Equation",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.duration): "Duration",
            (QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole, self.column.repetitions): "Repetitions"
            }
        self.dataLookup = {
            (QtCore.Qt.DisplayRole, self.column.position): lambda node: node.position
            if ((node.nodeType == nodeTypes.segment or node.nodeType == nodeTypes.segmentSet) and node.parent ==
                self.root and node.enabled is True) else None,
            (QtCore.Qt.CheckStateRole,self.column.enabled): lambda node: QtCore.Qt.Checked if node.enabled else QtCore.Qt.Unchecked,
            (QtCore.Qt.DisplayRole, self.column.name): lambda node: node.name if (node.nodeType==nodeTypes.segment or node.nodeType == nodeTypes.segmentSet) else None,
            (QtCore.Qt.DisplayRole, self.column.equation): lambda node: node.equation if node.nodeType==nodeTypes.segment else None,
            (QtCore.Qt.DisplayRole, self.column.duration): lambda node:  node.duration if node.nodeType==nodeTypes.segment else None,
            (QtCore.Qt.DisplayRole, self.column.repetitions): lambda node:  node.repetitions if node.nodeType==nodeTypes.segmentSet else None,
            (QtCore.Qt.BackgroundColorRole, self.column.position): lambda node: self.colorCode(node)
            if node.parent != self.root or node.childCount() != 0 else None,
            (QtCore.Qt.BackgroundColorRole, self.column.enabled): lambda node: self.colorCode(node)
            if node.parent != self.root or node.childCount() != 0 else None,
            (QtCore.Qt.BackgroundColorRole, self.column.name): lambda node: self.colorCode(node)
            if node.parent != self.root or node.childCount() != 0 else None,
            (QtCore.Qt.BackgroundColorRole, self.column.equation): lambda node: self.colorCode(node)
            if node.parent != self.root or node.childCount() != 0 else None,
            (QtCore.Qt.BackgroundColorRole, self.column.duration): lambda node: self.colorCode(node)
            if node.parent != self.root or node.childCount() != 0 else None,
            (QtCore.Qt.BackgroundColorRole, self.column.repetitions): lambda node: self.colorCode(node)
            if node.parent != self.root or node.childCount() != 0 else None,
            (QtCore.Qt.EditRole, self.column.position): lambda node: node.position
            if ((node.nodeType == nodeTypes.segment or node.nodeType == nodeTypes.segmentSet) and node.parent ==
                self.root and node.enabled is True) else None,
            (QtCore.Qt.EditRole, self.column.name): lambda node: node.name if (node.nodeType==nodeTypes.segment or node.nodeType == nodeTypes.segmentSet) else None,
            (QtCore.Qt.EditRole, self.column.equation): lambda node: node.equation if node.nodeType==nodeTypes.segment else None,
            (QtCore.Qt.EditRole, self.column.duration): lambda node:  node.duration if node.nodeType==nodeTypes.segment else None,
            (QtCore.Qt.EditRole, self.column.repetitions): lambda node:  node.repetitions if node.nodeType==nodeTypes.segmentSet else None
            }
        self.setDataLookup = {
            (QtCore.Qt.EditRole, self.column.position): lambda index, value: self.setValue(index, value, 'position'),
            (QtCore.Qt.CheckStateRole, self.column.enabled): lambda index, value: self.setEnabled(index, value),
            (QtCore.Qt.EditRole, self.column.name): lambda index, value: self.setValue(index, value, 'name'),
            (QtCore.Qt.EditRole, self.column.equation): lambda index, value: self.setValue(index, value, 'equation'),
            (QtCore.Qt.EditRole, self.column.duration): lambda index, value: self.setValue(index, value, 'duration'),
            (QtCore.Qt.EditRole, self.column.repetitions): lambda index, value: self.setValue(index, value, 'repetitions'),
            }

    def getSuperParent(self, node):
        """This finds the highest level parent that is not root"""
        if node.parent != self.root:
            return self.getSuperParent(node.parent)
        else:
            return node

    def colorCode(self, node):
        """This assigns colors to groups in the AWG"""
        parent = self.getSuperParent(node)
        if parent in self.colorDict:
            return self.colorDict[parent]
        else:
            self.colorDict[node] = self.colorList[self.incrementor]
            if self.incrementor == 9:
                self.incrementor = 0
            else:
                self.incrementor += 1
            return self.colorDict[node]


    def nodeFromIndex(self, index):
        """Return the node at the given index"""
        return index.internalPointer() if index.isValid() else self.root

    def indexFromNode(self, node, col=0):
        """Return a model index for the given node column"""
        if node == self.root:
            return QtCore.QModelIndex()
        else:
            parentIndex = QtCore.QModelIndex() if node.parent==self.root else self.indexFromNode(node.parent) #recursive
            return self.index(node.row, col, parentIndex)

    def index(self, row, column, parentIndex):
        """Return a model index for the node at the given row, column, parentIndex"""
        if not self.hasIndex(row, column, parentIndex):
            ind = QtCore.QModelIndex()
        else:
            parentNode = self.nodeFromIndex(parentIndex)
            node = parentNode.child(row)
            ind = self.createIndex(row, column, node) if node else QtCore.QModelIndex()
        return ind

    def rowCount(self, index):
        node = self.nodeFromIndex(index)
        return node.childCount()

    def columnCount(self, index):
        return self.numColumns

    def data(self, index, role):
        node = self.nodeFromIndex(index)
        col = index.column()
        return self.dataLookup.get((role, col), lambda node: None)(node)

    def setData(self, index, value, role):
        return self.setDataLookup.get( (role, index.column()), lambda index, value: False)(index, value)

    def parent(self, index):
        node = self.nodeFromIndex(index)
        parentNode = node.parent
        return QtCore.QModelIndex() if (node == self.root or parentNode == self.root) else self.createIndex(parentNode.row, 0, parentNode)

    def flags(self, index):
        node = self.nodeFromIndex(index)
        col = index.column()

        if col==self.column.enabled:
            return QtCore.Qt.ItemIsEnabled |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | \
                   QtCore.Qt.ItemIsDropEnabled
        elif col==self.column.position and (node.nodeType==nodeTypes.segment or node.nodeType==nodeTypes.segmentSet):
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | \
                   QtCore.Qt.ItemIsDropEnabled
        elif col==self.column.name and (node.nodeType==nodeTypes.segment or node.nodeType==nodeTypes.segmentSet):
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | \
                   QtCore.Qt.ItemIsDropEnabled
        elif col==self.column.equation and node.nodeType==nodeTypes.segment:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | \
                   QtCore.Qt.ItemIsDropEnabled
        elif col==self.column.duration and node.nodeType==nodeTypes.segment:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | \
                   QtCore.Qt.ItemIsDropEnabled
        elif col==self.column.repetitions and node.nodeType==nodeTypes.segmentSet:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | \
                   QtCore.Qt.ItemIsDropEnabled
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled | \
                   QtCore.Qt.ItemIsDropEnabled

    def headerData(self, section, orientation, role):
        return self.headerLookup.get((orientation, role, section))

    def setEnabled(self, index, value):
        node = self.nodeFromIndex(index)
        node.enabled = value==QtCore.Qt.Checked
        for childNode in node.children:
            childIndex = self.indexFromNode(childNode)
            self.setEnabled(childIndex, value) #recursive
        self.dataChanged.emit(index, index)
        self.segmentChanged.emit()
        self.settings.saveIfNecessary()
        return True

    def setValue(self, index, value, key):
        node = self.nodeFromIndex(index)
        if (node.nodeType==nodeTypes.segment and (key=='equation' or key=='duration')) or \
                (node.nodeType==nodeTypes.segmentSet and key=='repetitions'):
            strvalue = str(value)
            if strvalue in self.globalDict:
                logging.getLogger(__name__).warning("'{0}' is already a global variable name".format(strvalue))
                return False
            elif (not isIdentifier(strvalue)) and (not isValueExpression(strvalue)) and index.column()!=self.column.equation:
                logging.getLogger(__name__).warning("'{0}' is not a valid variable name or value".format(strvalue))
                return False
            else:
                setattr(node, key, strvalue)
                self.dataChanged.emit(index, index)
                self.segmentChanged.emit()
                self.settings.saveIfNecessary()
                return True
        elif (node.nodeType==nodeTypes.segment and (key=='name')) or \
              (node.nodeType==nodeTypes.segmentSet and key=='name'):
            strvalue = str(value)
            setattr(node, key, strvalue)
            self.dataChanged.emit(index, index)
            self.segmentChanged.emit()
            self.settings.saveIfNecessary()
            return True
        elif (node.nodeType == nodeTypes.segment and (key == 'position')) or \
                (node.nodeType == nodeTypes.segmentSet and key == 'position'):
            """This if branch is what adjusts the position of the row"""
            strvalue = str(value)
            try:
                int(strvalue)
                isAnInt = True
            except ValueError:
                isAnInt = False

            if isAnInt is True:
                newRow = int(strvalue) + 1

            setattr(node, key, newRow - 1)
            self.dataChanged.emit(index, index)
            self.positionChanged.emit()
            self.settings.saveIfNecessary()
            return True
        else:
            return False

    def addNode(self, parent, nodeType, row=None):
        parentIndex = self.indexFromNode(parent)
        node = AWGSegment(parent) if nodeType==nodeTypes.segment else AWGSegmentSet(parent)
        if row is None:
            row = parent.childCount()
            node.position = row + 1
        else:
            node.position = row
        self.beginInsertRows(parentIndex, row, row)
        parent.children.insert(row, node)
        self.endInsertRows()
        return node

    def moveRow(self, index, up):
        """move modelIndex 'index' up if up is True, else down"""
        node=self.nodeFromIndex(index)
        delta = -1 if up else 1
        parentIndex=self.indexFromNode(node.parent)
        if 0 <= node.row+delta < len(node.parent.children):
            moveValid = self.beginMoveRows(parentIndex, node.row, node.row, parentIndex, node.row-1 if up else node.row+2)
            if moveValid:
                node.row += delta
                self.endMoveRows()
                return True

    def changeParent(self, nodeList, oldParent, newParent, newParentRow=0):
        nodeList.sort(key = lambda node: node.row)
        firstRow = nodeList[0].row
        lastRow = nodeList[-1].row
        oldParentIndex = self.indexFromNode(oldParent)
        newParentIndex = self.indexFromNode(newParent)
        moveValid = self.beginMoveRows(oldParentIndex, firstRow, lastRow, newParentIndex, newParentRow)
        if moveValid:
            newParent.children[newParentRow:newParentRow] = nodeList
            for node in nodeList:
                node.parent = newParent
                if node in oldParent.children:
                    oldParent.children.remove(node)
            self.endMoveRows()
            return True

    def removeNode(self, node):
        """Remove the specified node from the tree."""
        if node.children==[] and node!=self.root:
            parent = node.parent
            row = node.row
            parentIndex = self.indexFromNode(parent)
            self.beginRemoveRows(parentIndex, row, row)
            del parent.children[row]
            self.endRemoveRows()

class AWGSegmentView(QtWidgets.QTreeView):
    segmentChanged = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(AWGSegmentView, self).__init__(parent)
        self.filter = KeyListFilter( [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown, QtCore.Qt.Key_Delete], [] )
        self.filter.keyPressed.connect(self.onKey)
        self.filter.controlKeyPressed.connect(self.onControlKey)
        self.installEventFilter(self.filter)

    def onKey(self, key):
        if key==QtCore.Qt.Key_Delete:
            self.onDelete()
        elif key in [QtCore.Qt.Key_PageUp, QtCore.Qt.Key_PageDown]:
            up = key==QtCore.Qt.Key_PageUp
            self.onReorder(up)

    def onControlKey(self, key):
        pass

    def onDelete(self):
        model = self.model()
        indexList = self.selectedRowIndexes()
        nodeList = [model.nodeFromIndex(index) for index in indexList]
        for node in nodeList:
            model.removeNode(node)
        self.segmentChanged.emit()

    def adjustPositions(self):
        """This function adjusts the positions columns of the elements in the AWG Table"""
        counter = 1
        model = self.model()
        self.selectAll()
        indexList = self.selectedRowIndexes()
        nodeList = [model.nodeFromIndex(index) for index in indexList]
        for node in nodeList:
            if node.position != counter:
                node.position = counter
            if node.parent == self.model().root and node.enabled is True:
                counter += 1
        self.clearSelection()

    def selectedRowIndexes(self):
        """Same as selectedRows, but returns list of nodes rather than list of model indexes"""
        allIndexList = self.selectedIndexes()
        indexList = []
        for index in allIndexList:
            if index.column()==0:
                indexList.append(index)
        indexList.sort(key=lambda index: index.row())
        return indexList

    def getIndex(self, rowName):
        """Scripting function used to get the index from a rowNumber, returns a tuple. """
        model = self.model()
        self.selectAll()
        indexList = self.selectedIndexes()
        rowIndexes = [model.nodeFromIndex(index) for index in indexList]
        counter = 0
        counter2 = 0

        for node in rowIndexes:
            if rowName == node.name:
                enabledOrDisabledBool = node.enabled
                break
            else:
                counter += 1

        for index in indexList:
            if counter2 == counter:
                self.clearSelection()
                return (index,enabledOrDisabledBool)
            else:
                counter2 += 1

        self.clearSelection()
        return None

    def onReorder(self, up):
        model = self.model()
        indexList = self.selectedRowIndexes()
        if not up:
            indexList.reverse()
        for index in indexList:
            model.moveRow(index, up)
        self.segmentChanged.emit()

    def getExpansionState(self, node):
        expansionList = []
        for childNode in node.children:
            expanded = self.isExpanded(self.model().indexFromNode(childNode))
            expansionList.append((expanded, self.getExpansionState(childNode)))
        return expansionList

    def restoreExpansionState(self, node, expansionList):
        try:
            for row, childNode in enumerate(node.children):
                index = self.model().indexFromNode(childNode)
                self.setExpanded(index, expansionList[row][0])
                self.restoreExpansionState(childNode, expansionList[row][1])
        except IndexError:
            logging.getLogger(__name__).warning("Unable to restore tree state")

    def saveTreeState(self):
        columnWidths = self.header().saveState()
        expansionState = self.getExpansionState(self.model().root)
        return {'columnWidths':columnWidths,
                'expansionState':expansionState}

    def restoreTreeState(self, state):
        if state:
            if 'columnWidths' in state:
                self.header().restoreState(state['columnWidths'])
            if 'expansionState' in state:
                self.restoreExpansionState(self.model().root, state['expansionState'])

    def dragEnterEvent(self, e):
        """This method extracts the name from the row for the drag and drop operation"""
        model = self.model()
        indexList = self.selectedIndexes()
        nodeList = [model.nodeFromIndex(index) for index in indexList]
        e.mimeData().setText(nodeList[0].name)
        e.accept()

    def dropEvent(self, e):
        """This method extracts the row number from the old row position for the drag and drop operation"""
        model = self.model()
        # This is important, this indicates where in relation to the index it is dropped
        # print(self.dropIndicatorPosition())
        nodeList = [model.nodeFromIndex(index) for index in [self.indexAt(e.pos())]]
        model.setValue(self.getIndex(e.mimeData().text())[0], nodeList[0].position, "position")
