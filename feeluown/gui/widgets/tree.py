from typing import Optional, List

from PyQt5.QtCore import Qt, QAbstractItemModel, QModelIndex
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem


class TreeNode:

    def __init__(
        self,
        data,
        children: Optional[List['TreeNode']] = None,
        parent: Optional['TreeNode'] = None,
    ):
        self.data = data
        self.children = children or []
        self.parent = parent

    def append_child(self, item):
        self.children.append(item)

    def child(self, row) -> 'TreeNode':
        return self.children[row]

    def row_count(self):
        return len(self.children)

    def column_count(self):
        return 1

    def parent(self):
        return self.parent


class TreeModel(QAbstractItemModel):

    def __init__(self, root: TreeNode):
        super().__init__()

        self.root = root

    def index(self, row, column, parent=QModelIndex()):
        if parent:
            node = parent.data(Qt.UserRole)
            if column > 1:
                return QModelIndex()
            return node.child(row)
        return QModelIndex()

    def rowCount(self, parent=QModelIndex()):
        return len(self.root.children)

    def columnCount(self, _=QModelIndex()):
        return 1

    def data(self, index, role=Qt.DisplayRole):
        node = self.root.child(index.row())
        if role == Qt.UserRole:
            return node
        elif role == Qt.DisplayRole:
            return node.data
        return None


if __name__ == "__main__":
    from feeluown.gui.debug import simple_layout

    root = TreeNode('动听音乐')
    root.children = [
        TreeNode('我的收藏', children=[TreeNode('歌单'), TreeNode('专辑')]),
        TreeNode('我的音乐', children=[TreeNode('私人FM'), TreeNode('云盘')]),
        TreeNode('发现', children=[TreeNode('歌单'), TreeNode('排行榜')]),
    ]

    root1 = QTreeWidgetItem(['动听音乐'])
    child1 = QTreeWidgetItem(root1, ['我的收藏'])
    root1.addChild(child1)
    root1.addChild(QTreeWidgetItem(root1, ['我的音乐']))
    root1.addChild(QTreeWidgetItem(root1, ['发现']))
    child1.addChild(QTreeWidgetItem(['歌单']))
    child1.addChild(QTreeWidgetItem(['专辑']))

    root2 = QTreeWidgetItem(['动听音乐'])
    child1 = QTreeWidgetItem(root2, ['我的收藏'])
    root2.addChild(child1)
    root2.addChild(QTreeWidgetItem(root2, ['我的音乐']))
    root2.addChild(QTreeWidgetItem(root2, ['发现']))
    child1.addChild(QTreeWidgetItem(['歌单']))
    child1.addChild(QTreeWidgetItem(['专辑']))

    with simple_layout() as layout:
        view = QTreeWidget()
        # view.setIndentation(4)
        view.addTopLevelItem(root1)
        view.addTopLevelItem(root2)
        layout.addWidget(view)
