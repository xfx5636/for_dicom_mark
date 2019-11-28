from __future__ import division
# from Tkinter import *
# import tkMessageBox
# from tkinter import messagebox
from tkinter import *
from PIL import Image, ImageTk
import os
import glob
import random
import pydicom
import os
import shutil
import xml.dom.minidom
import xml.dom
import codecs
import matplotlib.pyplot as plt
import cv2
import numpy as np
from PIL import Image

w0 = 1  # 图片原始宽度
h0 = 1  # 图片原始高度

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 256, 256

# 指定缩放后的图像大小
DEST_SIZE = 500, 500


class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width=TRUE, height=TRUE)
        self.patientID = getPatientCode(os.path.join(os.getcwd(), 'data', 'source'))
        print(self.patientID)
        # store patientID as a property

        # initialize global state
        self.imageDir = ''
        self.ctDir = ''
        self.imageCtList = []
        self.imageList = []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.labelfilename_node = ''
        self.labelfilename_pt = ''
        self.labelfilename_pt_node = ''
        self.tkimg = None
        self.tk_ct_img = None
        self.node_num = 0

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.nameBox = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text="Image Dir:")
        self.label.grid(row=0, column=0, sticky=E)
        self.entry = Entry(self.frame)
        self.entry.grid(row=0, column=1, sticky=W + E)
        self.ldBtn = Button(self.frame, text="Load", command=self.loadDir)
        self.ldBtn.grid(row=0, column=2, sticky=W + E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("a", self.prevImage)  # press 'a' to go backforward
        self.parent.bind("d", self.nextImage)  # press 'd' to go forward
        self.mainPanel.grid(row=1, column=1, rowspan=4, sticky=W + N)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text='Bounding boxes:')
        self.lb1.grid(row=1, column=2, sticky=W + N)

        self.listbox = Listbox(self.frame, width=28, height=6)
        self.listbox.grid(row=2, column=2, sticky=N)

        self.btnDel = Button(self.frame, text='Delete', command=self.delBBox)
        self.btnDel.grid(row=3, column=2, sticky=W + E + N)
        self.btnClear = Button(self.frame, text='ClearAll', command=self.clearBBox)
        self.btnClear.grid(row=4, column=2, sticky=W + E + N)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row=5, column=1, columnspan=2, sticky=W + E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width=10, command=self.prevImage)
        self.prevBtn.pack(side=LEFT, padx=5, pady=3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width=10, command=self.nextImage)
        self.nextBtn.pack(side=LEFT, padx=5, pady=3)
        self.progLabel = Label(self.ctrPanel, text="Progress:     /    ")
        self.progLabel.pack(side=LEFT, padx=5)
        self.tmpLabel = Label(self.ctrPanel, text="Go to Image No.")
        self.tmpLabel.pack(side=LEFT, padx=5)
        self.idxEntry = Entry(self.ctrPanel, width=5)
        self.idxEntry.pack(side=LEFT)
        self.goBtn = Button(self.ctrPanel, text='Go', command=self.gotoImage)
        self.goBtn.pack(side=LEFT)
        self.nodeBtn = Button(self.ctrPanel, text='标记非结点', command=self.switch_node)
        self.nodeBtn.pack(side=LEFT)

        # example pannel for illustration
        self.egPanel = Frame(self.frame, border=10)
        self.egPanel.grid(row=1, column=0, rowspan=5, sticky=N)
        self.tmpLabel2 = Label(self.egPanel, text="Slice Location:")
        self.listbox2 = Listbox(self.frame, width=28, height=6)
        self.listbox2.grid(row=3, column=0, sticky=W+N)
        self.tmpLabel2.pack(side=TOP, pady=5)

        self.egLabels = []
        for i in range(3):
            self.egLabels.append(Label(self.egPanel))
            self.egLabels[-1].pack(side=TOP)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side=RIGHT)

        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(4, weight=1)

        # for debugging

    ##        self.setImage()
    ##        self.loadDir()


    def loadDir(self, dbg=False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.category = str(s)
        else:
            s = os.path.join(os.getcwd(), 'images', str(self.patientID)) # r'E:/SearchQA/SearchQA/images/FDG34184'
        ##        if not os.path.isdir(s):
        ##            tkMessageBox.showerror("Error!", message = "The specified dir doesn't exist!")
        ##            return
        # get image list

        print('self.category =%s' % (self.category))

        self.imageDir = os.path.join(r'./images/%s' % self.category, 'pt')
        self.ctDir = os.path.join(r'./images/%s' % self.category, 'ct')
        self.imageCtList = glob.glob(os.path.join(self.ctDir, '*.jpg'))
        print(self.imageDir)
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        if len(self.imageList) == 0:
            print('No .jpg images found in the specified dir!')
            return
        else:
            print('num=%d' % (len(self.imageList)))
        self.imageList = sorted(self.imageList, key=lambda x: float(x.strip('.jpg').split('\\')[-1]), reverse=FALSE)
        self.imageCtList = sorted(self.imageCtList, key=lambda x: float(x.strip('.jpg').split('\\')[-1]), reverse=FALSE)
        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

        # set up output dir
        self.outDir = os.path.join(os.getcwd(),'labels', self.category)
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)
            os.mkdir(os.path.join(self.outDir, 'ct'))
            os.mkdir(os.path.join(self.outDir, 'pt'))

        # load example bboxes
        self.egDir = os.path.join(r'./Examples', '%s' % (self.category))
        # if not os.path.exists(self.egDir):
        #   return

        filelist = glob.glob(os.path.join(self.egDir, '*.jpg'))
        self.tmp = []
        self.egList = []
        random.shuffle(filelist)
        for (i, f) in enumerate(filelist):
            if i == 3:
                break
            im = Image.open(f)
            r = min(SIZE[0] / im.size[0], SIZE[1] / im.size[1])
            new_size = int(r * im.size[0]), int(r * im.size[1])
            # xfx
            # self.tmp.append(im.resize(new_size, Image.ANTIALIAS))
            # self.egList.append(ImageTk.PhotoImage(self.tmp[-1]))
            # self.egLabels[i].config(image=self.egList[-1], width=SIZE[0], height=SIZE[1])
            self.tmp.append(im.resize(new_size, Image.ANTIALIAS))
            self.egList.append(ImageTk.PhotoImage(self.tmp[-1]))
            self.egLabels[i].config(image=self.egList[-1], width=SIZE[0], height=SIZE[1])

        self.loadImage()
        print('%d images loaded from %s' % (self.total, s))

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        pil_image = Image.open(imagepath)
        image_ct_path = self.imageCtList[self.cur - 1]
        pil_ct_image = Image.open(image_ct_path)

        # get the size of the image
        # 获取图像的原始大小
        global w0, h0
        w0, h0 = pil_image.size

        # 缩放到指定大小
        pil_image = pil_image.resize((DEST_SIZE[0], DEST_SIZE[1]), Image.ANTIALIAS)
        pil_ct_image = pil_ct_image.resize((DEST_SIZE[0], DEST_SIZE[1]), Image.ANTIALIAS)
        # pil_image = imgresize(w, h, w_box, h_box, pil_image)
        self.img = pil_image
        self.ct_img = pil_ct_image

        self.tkimg = ImageTk.PhotoImage(pil_image)
        self.tk_ct_img = ImageTk.PhotoImage(pil_ct_image)

        self.mainPanel.config(width=max(self.tkimg.width(), 1000), height=max(self.tkimg.height(), 500))
        self.mainPanel.create_image(0, 0, image=self.tk_ct_img, anchor=NW)
        self.mainPanel.create_image(500, 0, image=self.tkimg, anchor=NW)
        self.progLabel.config(text="%04d/%04d" % (self.cur, self.total))

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].strip('.jpg')
        labelname = self.imagename
        if not os.path.exists(os.path.join(os.path.join(self.outDir, 'ct'))):
            os.mkdir(os.path.join(os.path.join(self.outDir, 'ct')))
        if not os.path.exists(os.path.join(os.path.join(self.outDir, 'pt'))):
            os.mkdir(os.path.join(os.path.join(self.outDir, 'pt')))
        self.labelfilename = os.path.join(os.path.join(self.outDir, 'ct'), labelname+'_non_node.txt')
        self.labelfilename_node = os.path.join(os.path.join(self.outDir, 'ct'), labelname+'_node.txt')
        self.labelfilename_pt = os.path.join(os.path.join(self.outDir, 'pt'), labelname+'_non_node.txt')
        self.labelfilename_pt_node = os.path.join(os.path.join(self.outDir, 'pt'), labelname+'_node.txt')
        self.nameBox.append(imagepath.split('\\')[-1])
        self.listbox2.insert(END, '%s' % imagepath.split('\\')[-1])

        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                f_lines = f.readlines()
                with open(self.labelfilename_node) as f_node:
                    f_node_lines = f_node.readlines()
                    f_lines.extend(f_node_lines[1:])
                    with open(self.labelfilename_pt) as f_pt:
                        pt_lines = f_pt.readlines()
                        f_lines.extend(pt_lines[1:])
                        with open(self.labelfilename_pt_node) as f_pt_node:
                            f_pt_node_lines = f_pt_node.readlines()
                            f_lines.extend(f_pt_node_lines[1:])
                            for (i, line) in enumerate(f_lines):
                                if i == 0:
                                    bbox_cnt = int(line.strip())
                                    continue
                                print(line)
                                tmp = [(t.strip()) for t in line.split()]

                                print("********************")
                                print(DEST_SIZE)
                                # tmp = (0.1, 0.3, 0.5, 0.5)
                                print("tmp[0,1,2,3]===%.2f, %.2f, %.2f, %.2f" % (
                                    float(tmp[0]), float(tmp[1]), float(tmp[2]), float(tmp[3])))
                                # print "%.2f,%.2f,%.2f,%.2f" %(tmp[0] tmp[1] tmp[2] tmp[3] )

                                print("********************")

                                # tx = (10, 20, 30, 40)
                                # self.bboxList.append(tuple(tx))
                                self.bboxList.append(tuple(tmp))
                                tmp[0] = float(tmp[0])
                                tmp[1] = float(tmp[1])
                                tmp[2] = float(tmp[2])
                                tmp[3] = float(tmp[3])

                                tx0 = int(tmp[0] * DEST_SIZE[0])
                                ty0 = int(tmp[1] * DEST_SIZE[1])

                                tx1 = int(tmp[2] * DEST_SIZE[0])
                                ty1 = int(tmp[3] * DEST_SIZE[1])

                                print("tx0, ty0, tx1, ty1")
                                print(tx0, ty0, tx1, ty1)

                                tmpId = self.mainPanel.create_rectangle(tx0, ty0, tx1, ty1,
                                                                        width=2,
                                                                        outline=COLORS[(len(self.bboxList) - 1) % len(COLORS)])

                                self.bboxIdList.append(tmpId)
                                self.listbox.insert(END, '(%.2f,%.2f)-(%.2f,%.2f)' % (tmp[0], tmp[1], tmp[2], tmp[3]))

                                # self.listbox.insert(END, '(%d, %d) -> (%d, %d)' %(tmp[0], tmp[1], tmp[2], tmp[3]))
                                self.listbox.itemconfig(len(self.bboxIdList) - 1,
                                                        fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def saveImage(self):
        # print "-----1--self.bboxList---------"
        print(self.bboxList)
        # print "-----2--self.bboxList---------"
        print('node num is : %d' % self.node_num)
        node_list = self.bboxList[: len(self.bboxList)-self.node_num]
        non_node_list = self.bboxList[(len(self.bboxList)-self.node_num):]
        node_pt_list = []
        node_ct_list = []
        non_node_pt_list = []
        non_node_ct_list = []
        for node in node_list:
            if float(node[0]) < 1:
                node_ct_list.append(node)
            else:
                node_pt_list.append(node)
        for node in non_node_list:
            if float(node[0]) < 1:
                non_node_ct_list.append(node)
            else:
                non_node_pt_list.append(node)
        with open(self.labelfilename, 'w') as f:
            f.write('%d\n' % len(non_node_ct_list))
            for bbox in non_node_ct_list:
                f.write(' '.join(map(str, bbox)) + '\n')
        with open(self.labelfilename_node, 'w') as f:
            f.write('%d\n' % len(node_ct_list))
            for bbox in node_ct_list:
                f.write(' '.join(map(str, bbox)) + '\n')
        with open(self.labelfilename_pt, 'w') as f:
            f.write('%d\n' % len(non_node_pt_list))
            for bbox in non_node_pt_list:
                f.write(' '.join(map(str, bbox)) + '\n')
        with open(self.labelfilename_pt_node, 'w') as f:
            f.write('%d\n' % len(node_pt_list))
            for bbox in node_pt_list:
                f.write(' '.join(map(str, bbox)) + '\n')
        print('Image No. %d saved' % (self.cur))

    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            if self.nodeBtn['text'] == '标记节点':
                self.node_num += 1
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            # x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            # y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            #
            # x1, x2 = x1 / DEST_SIZE[0], x2 / DEST_SIZE[0];
            # y1, y2 = y1 / DEST_SIZE[1], y2 / DEST_SIZE[1];
            x1, x2 = min(self.STATE['x'], self.STATE['x']+1), max(self.STATE['x'], self.STATE['x']+1)
            y1, y2 = min(self.STATE['y'], self.STATE['y']+1), max(self.STATE['y'], self.STATE['y']+1)

            x1, x2 = x1 / DEST_SIZE[0], x2 / DEST_SIZE[0]
            y1, y2 = y1 / DEST_SIZE[1], y2 / DEST_SIZE[1]
            self.bboxList.append((x1, y1, x2, y2))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '(%.2f, %.2f)-(%.2f, %.2f)' % (x1, y1, x2, y2))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text='x: %.2f, y: %.2f' % (event.x / DEST_SIZE[0], event.y / DEST_SIZE[1]))
        # if self.tkimg:
        #     if self.hl:
        #         self.mainPanel.delete(self.hl)
        #     self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width=2)
        #     if self.vl:
        #         self.mainPanel.delete(self.vl)
        #     self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width=2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'],
                                                          self.STATE['x']+1, self.STATE['y']+1,
                                                          width=2,
                                                          outline=COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])

        self.listbox.delete(0, len(self.bboxList))
        self.listbox2.delete(0, len(self.nameBox))
        self.bboxIdList = []
        self.bboxList = []
        self.nameBox = []

    def prevImage(self, event=None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event=None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

    def switch_node(self):
        if self.nodeBtn['text'] == '标记非结点':
            self.nodeBtn['text'] = '标记节点'
            print(1)
        else:
            self.nodeBtn['text'] = '标记非节点'

    ##    def setImage(self, imagepath = r'test2.png'):
    ##        self.img = Image.open(imagepath)
    ##        self.tkimg = ImageTk.PhotoImage(self.img)
    ##        self.mainPanel.config(width = self.tkimg.width())
    ##        self.mainPanel.config(height = self.tkimg.height())
    ##        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)

    def imgresize(self, w, h, w_box, h_box, pil_image):
        '''
        resize a pil_image object so it will fit into
        a box of size w_box times h_box, but retain aspect ratio
        '''
        f1 = 1.0 * w_box / w  # 1.0 forces float division in Python2
        f2 = 1.0 * h_box / h
        factor = min([f1, f2])
        # print(f1, f2, factor) # test
        # use best down-sizing filter
        width = int(w * factor)
        height = int(h * factor)
        return pil_image.resize((width, height), Image.ANTIALIAS)


def nothing(x):
    pass


def makeEasyTag(dom, tagname, value, type='text'):
    tag = dom.createElement(tagname)
    if value.find(']]>') > -1:
        type = 'text'
    if type == 'text':
        value = value.replace('&', '&amp;')
        value = value.replace('<', '&lt;')
        text = dom.createTextNode(value)
    elif type == 'cdata':
        text = dom.createCDATASection(value)
    tag.appendChild(text)
    return tag


def Indent(dom, node, indent=0):
    # Copy child list because it will change soon
    children = node.childNodes[:]
    # Main node doesn't need to be indented

    if indent:
        text = dom.createTextNode('\n' + '\t' * indent)
        node.parentNode.insertBefore(text, node)
    if children:
        # Append newline after last child, except for text nodes
        if children[-1].nodeType == node.ELEMENT_NODE:
            text = dom.createTextNode('\n' + '\t' * indent)
            node.appendChild(text)
            # Indent children which are elements
            for n in children:
                if n.nodeType == node.ELEMENT_NODE:
                    Indent(dom, n, indent + 1)


def add_nodules(dom, parent_node, num_nodule, xy, modality, instance_number, sop_instance_uid):
    unblinded_read_nodule = makeEasyTag(dom, 'unblindedReadNodule', '')
    parent_node.appendChild(unblinded_read_nodule)
    if 0 < num_nodule < 10:
        nodule_nums_str = '00' + str(num_nodule)
    elif 10 <= num_nodule < 100:
        nodule_nums_str = '0' + str(num_nodule)
    else:
        nodule_nums_str = str(num_nodule)
    nodule_id = makeEasyTag(dom, 'noduleID', 'Nodule %s' % nodule_nums_str)
    unblinded_read_nodule.appendChild(nodule_id)
    roi = makeEasyTag(dom, 'roi', '')
    unblinded_read_nodule.appendChild(roi)
    # Indent(dom, unblinded_read_nodule, 1)
    # instance_num = makeEasyTag(dom, 'InstanceNumber_%s' % Y.Modality, str(Y.InstanceNumber))
    # SOP_instance_UID = makeEasyTag(dom, 'SOPInstanceUID_%s' % Y.Modality, str(Y.SOPInstanceUID))
    instance_num = makeEasyTag(dom, 'InstanceNumber_%s' % modality, str(instance_number))
    SOP_instance_UID = makeEasyTag(dom, 'SOPInstanceUID_%s' % modality, str(sop_instance_uid))
    edgeMap = makeEasyTag(dom, 'edgeMap_%s' % modality, '')
    roi.appendChild(instance_num)
    roi.appendChild(SOP_instance_UID)
    roi.appendChild(edgeMap)
    x_coord = makeEasyTag(dom, 'xCoord', str(xy[0][0]))
    y_coord = makeEasyTag(dom, 'yCoord', str(xy[0][1]))
    edgeMap.appendChild(x_coord)
    edgeMap.appendChild(y_coord)
    # Indent(dom, nodule_id, 1)
    # Indent(dom, roi, 1)
    # Indent(dom, edgeMap, 1)


def add_non_nodules(dom, parent_node, non_nodule_nums, xy, modality, instance_number, sop_instance_uid):
    unblinded_read_nodule = makeEasyTag(dom, 'nonNodule', '')
    parent_node.appendChild(unblinded_read_nodule)
    if 0 < non_nodule_nums < 10:
        non_nodule_nums_str = '00' + str(non_nodule_nums)
    elif 10 <= non_nodule_nums < 100:
        non_nodule_nums_str = '0' + str(non_nodule_nums)
    else:
        non_nodule_nums_str = str(non_nodule_nums)
    non_nodule_id = makeEasyTag(dom, 'nonNoduleID', 'Non-nodule %s' % non_nodule_nums_str)
    unblinded_read_nodule.appendChild(non_nodule_id)
    roi = makeEasyTag(dom, 'roi', '')
    unblinded_read_nodule.appendChild(roi)
    # Indent(dom, unblinded_read_nodule, 1)
    instance_num = makeEasyTag(dom, 'InstanceNumber_%s' % modality, str(instance_number))
    SOP_instance_UID = makeEasyTag(dom, 'SOPInstanceUID_%s' % modality, str(sop_instance_uid))
    edgeMap = makeEasyTag(dom, 'locus_%s' % modality, '')
    roi.appendChild(instance_num)
    roi.appendChild(SOP_instance_UID)
    roi.appendChild(edgeMap)
    x_coord = makeEasyTag(dom, 'xCoord', str(xy[0][0]))
    y_coord = makeEasyTag(dom, 'yCoord', str(xy[0][1]))
    edgeMap.appendChild(x_coord)
    edgeMap.appendChild(y_coord)
    # Indent(dom, non_nodule_id, 1)
    # Indent(dom, roi, 1)
    # Indent(dom, edgeMap, 1)


def align_ct_pt(ct_path):
    """
    :param ct_path: 去掉ct_path中文件大于1M的，description中有head和brain的dcm
    :return:
    """
    try:
        float(os.listdir(ct_path)[0].strip('.dcm'))
    except:
        for file in os.listdir(ct_path):
            if file == '.DS_Store':
                continue
            if os.path.getsize(os.path.join(ct_path, file)) >= 1049046:
                # print(os.path.getsize(ct_path + file))
                os.remove(os.path.join(ct_path, file))
                continue
            Y = pydicom.read_file(os.path.join(ct_path, file))
            if str(Y.SeriesDescription).split('-')[0] == 'Head' or 'Brain' in str(Y.SeriesDescription):
                os.remove(os.path.join(ct_path, file))
                # print(Y.SeriesDescription)
                continue
            # if str(Y.SliceLocation) + '.dcm' in os.listdir(ct_path):
            #     plt.figure()
            #     plt.subplot(1,2,1)
            #     plt.imshow(Y.pixel_array)
            #     plt.subplot(1,2,2)
            #     Y1 = pydicom.read_file(ct_path + str(Y.SliceLocation) + '.dcm')
            #     print(Y1.SeriesDescription, Y.SeriesDescription)
            #     plt.imshow(Y1.pixel_array)
            #     plt.show()
            #     break
            os.rename(os.path.join(ct_path, file), os.path.join(ct_path, str(Y.SliceLocation)+'.'+file.split('.')[-1]))


def get_align_dicom(ct_path, pt_path, pt_new_path):
    """
    :param ct_path:
    :param pt_path:
    :param pt_new_path: 插值后pt-dcm存储路径
    :return:
    """
    ct_file = []
    pt_file = []
    for file in os.listdir(ct_path):
        if file == '.DS_Store':
            continue
        ct_file.append([file, float(file.strip('.dcm'))])
    for file in os.listdir(pt_path):
        if file == '.DS_Store':
            continue
        pt_file.append([file, float(file.strip('.dcm'))])
    ct_file = sorted(ct_file, key=lambda x: x[1], reverse=False)
    pt_file = sorted(pt_file, key=lambda x: x[1], reverse=False)
    pt_file, pt_val = list(zip(*pt_file))
    count = 0
    for file, val in ct_file:
        if count == 0 or count == len(ct_file)-1:
            if val <= pt_val[0] or val >= pt_val[-1]:
                shutil.copyfile(os.path.join(pt_path, pt_file[count]), os.path.join(pt_new_path, pt_file[count]))
                os.rename(os.path.join(pt_path, pt_file[count]), os.path.join(pt_new_path, str(val)+'.dcm'))
                count += 1
                continue
        for pt_i in range(len(pt_val)-1):
            if pt_val[pt_i] < val <= pt_val[pt_i+1]:
                pre_weight = 1.0*(pt_val[pt_i+1]-val)/(pt_val[pt_i+1] - pt_val[pt_i])
                back_weigth = 1.0*(val-pt_val[pt_i])/(pt_val[pt_i+1] - pt_val[pt_i])

                pre_dcm = pydicom.read_file(os.path.join(pt_path, pt_file[pt_i]))
                pre_dcm_pix = pre_dcm.pixel_array

                back_dcm = pydicom.read_file(os.path.join(pt_path, pt_file[pt_i+1]))
                back_dcm_pix = back_dcm.pixel_array

                insert_pix = pre_weight*pre_dcm_pix + back_weigth*back_dcm_pix
                pre_dcm.SliceLocation = val
                if pre_dcm[0x0028, 0x0100].value == 16:  # 如果dicom文件矩阵是16位格式
                    newimg = insert_pix.astype(np.uint16)  # newimg 是图像矩阵 ds是dcm
                elif pre_dcm[0x0028, 0x0100].value == 8:
                    newimg = insert_pix.astype(np.uint8)
                else:
                    raise Exception("unknow Bits Allocated value in dicom header")
                pre_dcm.PixelData = newimg.tobytes()
                pre_dcm.save_as(os.path.join(pt_new_path,file))


def read_new_pt(pt_new_path):
    for file in os.listdir(pt_new_path):
        if file == '.DS_Store':
            continue
        Y = pydicom.read_file(os.path.join(pt_new_path, file))
        y_pix = Y.pixel_array
        print(file, Y.SliceLocation)
        # for row in y_pix:
        #     print(row)
        # break
        plt.figure()
        plt.imshow(y_pix)
        plt.show()


def div_ct_pet(source_path, ct_path, pt_path):
    """
    :param source_path:把源文件夹中ct和pt分开到各自文件夹中
    :param ct_path:
    :param pt_path:
    :return:
    """
    path = source_path
    CT_file = open(os.path.join(os.getcwd(),'xml','ct.txt'), 'w', encoding='utf8')
    PET_file = open(os.path.join(os.getcwd(),'xml','pet.txt'), 'w', encoding='utf8')
    for picture_name in os.listdir(path):
        if picture_name == '.DS_Store':
            continue
        Y = pydicom.read_file(os.path.join(path, picture_name))

        if Y.Modality == 'CT':
            shutil.copyfile(os.path.join(source_path, picture_name), os.path.join(ct_path, picture_name))
            CT_file.write(picture_name + '\n')
        else:
            PET_file.write(picture_name + '\n')
            shutil.copyfile(os.path.join(source_path, picture_name), os.path.join(pt_path, picture_name))
    CT_file.close()
    PET_file.close()


def trans_dcm_2_jpg(source_dcm_path, save_jpg_path, tag):
    for file in os.listdir(source_dcm_path):
        if file == '.DS_Store':
            continue
        print(tag, file)
        dcm = pydicom.dcmread(os.path.join(source_dcm_path, file))
        img_data = dcm.pixel_array
        dcm_img = Image.fromarray(img_data)
        dcm_img = dcm_img.convert('L')
        dcm_img.save(os.path.join(save_jpg_path, file.strip('.dcm') + '.jpg'))


def finally_save(patient_code, save_path, c_path, p_new_path, mark_result_path):
    error_list = []
    # 插值后可以通过CT的文件名，同时索引CT和PT文件
    path = []
    for sub_path in os.listdir(save_path):
        if sub_path.strip('_node.txt').strip('_node.txt') + '.dcm' not in path:
            path.append(sub_path.strip('_node.txt').strip('_node.txt') + '.dcm')
    path_sorted = sorted(path, key=lambda x: float(x.strip('.dcm')), reverse=False)
    print('已经标注了的图片有：', path_sorted)
    for picture_name in path_sorted:
        if picture_name == '.DS_Store':
            continue
        # try:
        # file_name = c_path.split('/')[-1]
        # print('=====',file_name)
        save_path = './xml/' + patient_code + '/'
        if not os.path.exists(save_path):
            os.mkdir(save_path)
        if (picture_name.split('.dcm')[0] + '.xml') in os.listdir(save_path):
            continue
        Y = pydicom.read_file(os.path.join(c_path, picture_name))
        Y_1 = pydicom.read_file(os.path.join(p_new_path, picture_name))
        Y_num = int(''.join(picture_name.split('.')).strip('dcm') + '1')

        mark_result_ct_path = os.path.join(mark_result_path, 'ct')
        mark_result_pt_path = os.path.join(mark_result_path, 'pt')
        node_ct_node_data = open(os.path.join(mark_result_ct_path, picture_name.strip('.dcm') + '_node.txt'), 'r',
                                 encoding='utf8').readlines()
        node_pt_node_data = open(os.path.join(mark_result_pt_path, picture_name.strip('.dcm') + '_node.txt'), 'r',
                                 encoding='utf8').readlines()
        non_node_ct_node_data = open(os.path.join(mark_result_ct_path, picture_name.strip('.dcm') + '_non_node.txt'),
                                     'r',
                                     encoding='utf8').readlines()
        non_node_pt_node_data = open(os.path.join(mark_result_pt_path, picture_name.strip('.dcm') + '_non_node.txt'),
                                     'r',
                                     encoding='utf8').readlines()
        if len(node_ct_node_data) == 1 and len(node_pt_node_data) == 1 and \
                len(non_node_ct_node_data) == 1 and len(non_node_pt_node_data) == 1:
            continue
        id_number = Y.AccessionNumber
        impl = xml.dom.minidom.getDOMImplementation()
        dom = impl.createDocument(None, 'LidcReadMessage', None)

        sub_dom1 = makeEasyTag(dom, 'ResponseHeader', '')
        sub_dom2 = makeEasyTag(dom, 'readingSession', '')
        root = dom.documentElement
        root.appendChild(sub_dom1)
        root.appendChild(sub_dom2)
        patient_name = makeEasyTag(dom, 'PatientName', Y.AccessionNumber)
        sub_dom1.appendChild(patient_name)
        date_service = makeEasyTag(dom, 'DateService', Y.ContentDate)
        sub_dom1.appendChild(date_service)
        study_instance = makeEasyTag(dom, 'StudyInstanceUID_%s' % Y.Modality, Y.StudyInstanceUID)
        series_instance = makeEasyTag(dom, 'SeriesInstanceUID_%s' % Y.Modality, Y.SeriesInstanceUID)
        study_instance_1 = makeEasyTag(dom, 'StudyInstanceUID_%s' % Y_1.Modality, Y.StudyInstanceUID)
        series_instance_1 = makeEasyTag(dom, 'SeriesInstanceUID_%s' % Y_1.Modality, Y.SeriesInstanceUID)
        sub_dom1.appendChild(study_instance)
        sub_dom1.appendChild(series_instance)
        sub_dom1.appendChild(study_instance_1)
        sub_dom1.appendChild(series_instance_1)

        list_node_i = 0
        if len(node_ct_node_data) > 1:
            for ct_node in node_ct_node_data[1:]:
                list_node_i += 1
                ct_node = ct_node.strip().split()
                add_nodules(dom, sub_dom2, list_node_i,
                            [[float(ct_node[0])*DEST_SIZE[0], float(ct_node[1])*DEST_SIZE[1]]], modality=Y.Modality,
                            instance_number=Y.InstanceNumber, sop_instance_uid=str(Y.SOPInstanceUID))
        if len(node_pt_node_data) > 1:
            for pt_node in node_pt_node_data[1:]:
                list_node_i += 1
                pt_node = pt_node.strip().split()
                add_nodules(dom, sub_dom2, list_node_i,
                            [[(float(pt_node[0])-1)*DEST_SIZE[0], float(pt_node[1])*DEST_SIZE[1]]],
                            modality=Y_1.Modality,
                            instance_number=Y_1.InstanceNumber, sop_instance_uid=str(Y_1.SOPInstanceUID))
        list_non_node_i = 0
        if len(non_node_ct_node_data) > 1:
            for ct_non_node in non_node_ct_node_data[1:]:
                list_non_node_i += 1
                ct_non_node = ct_non_node.strip().split()
                add_non_nodules(dom, sub_dom2, list_non_node_i,
                                [[float(ct_non_node[0])*DEST_SIZE[0], float(ct_non_node[1])*DEST_SIZE[1]]],
                                modality=Y.Modality,
                                instance_number=Y.InstanceNumber, sop_instance_uid=str(Y.SOPInstanceUID))
        if len(non_node_pt_node_data) > 1:
            for pt_non_node in non_node_pt_node_data[1:]:
                list_node_i += 1
                pt_non_node = pt_non_node.strip().split()
                add_non_nodules(dom, sub_dom2, list_non_node_i,
                                [[(float(pt_non_node[0])-1)*DEST_SIZE[0], float(pt_non_node[1])*DEST_SIZE[1]]],
                                modality=Y_1.Modality,
                                instance_number=Y_1.InstanceNumber, sop_instance_uid=str(Y_1.SOPInstanceUID))
        Indent(dom, sub_dom1, 1)
        Indent(dom, sub_dom2, 1)

        Indent(dom, root, 0)
        # item = makeEasyTag(dom, 'SeriesInstanceUID', Y.SeriesInstanceUID)
        # root.appendChild(item)
        f = open(save_path + str(picture_name.split('.dcm')[0]) + '.xml', 'wb')
        writer = codecs.lookup('utf-8')[3](f)
        dom.writexml(writer, encoding='utf-8')
        writer.close()
    print('出错误的图片有：', error_list)

def getPatientCode(source_path):
    '''
    To parse the Patient ID from dicom files in the folder specified
    '''
    Pcode = ''
    for ii in os.listdir(source_path):
        try:
            dcm_content = pydicom.dcmread(os.path.join(source_path,ii))
            Pcode = dcm_content.PatientID
        except:
            pass
        if len(Pcode) > 1:
            return Pcode
        
if __name__ == '__main__':
    source_path = os.path.join(os.getcwd(),'data','source') #'E:/SearchQA/for_dicom_mark/for_dicom_mark/data/FDG34184/'
    patient_code = getPatientCode(source_path)
    base_path = os.path.join(os.getcwd(),'data')
    image_path = os.path.join(os.getcwd(), 'images')
    label_path = os.path.join(os.getcwd(), 'labels')
    if not os.path.exists(os.path.join(base_path,patient_code+'_new')):
        os.mkdir(os.path.join(base_path,patient_code+'_new'))
    else:
        shutil.rmtree(os.path.join(base_path,patient_code+'_new'))
        os.mkdir(os.path.join(base_path,patient_code+'_new'))
        shutil.rmtree(os.path.join(os.getcwd(), 'images',patient_code))
        shutil.rmtree(os.path.join(os.getcwd(), 'labels',patient_code))
    patient_info_path = os.path.join(base_path,patient_code+'_new')
    # 把病人的CT和PT图片分开
    c_path = os.path.join(patient_info_path,'ct')
    p_path = os.path.join(patient_info_path,'pt')
    if not os.path.exists(c_path):
        os.mkdir(c_path)
    if not os.path.exists(p_path):
        os.mkdir(p_path)
    # 存储插值后的图片
    p_new_path = os.path.join(patient_info_path,'pt_new')
    if not os.path.exists(p_new_path):
        os.mkdir(p_new_path)
    if not os.path.exists(os.path.join(image_path, patient_code)):
        os.mkdir(os.path.join(image_path, patient_code))
    c_jpg_save_path = os.path.join(image_path, patient_code, 'ct') # r'E:\SearchQA\for_dicom_mark\for_dicom_mark\images\FDG34184\ct'
    p_jpg_save_path = os.path.join(image_path, patient_code, 'pt') # r'E:\SearchQA\for_dicom_mark\for_dicom_mark\images\FDG34184\pt'
    mark_result_path = os.path.join(label_path, patient_code) # r'E:\SearchQA\for_dicom_mark\for_dicom_mark\labels\FDG34184'
    if not os.path.exists(c_jpg_save_path):
        os.mkdir(c_jpg_save_path)
    if not os.path.exists(p_jpg_save_path):
        os.mkdir(p_jpg_save_path)
    if not os.path.exists(mark_result_path):
        os.mkdir(mark_result_path)
    print('====================开始分离CT和PT图片===========================\n')
    div_ct_pet(source_path=source_path, ct_path=c_path, pt_path=p_path)
    print('====================开始重命名CT图片===========================\n')
    align_ct_pt(ct_path=c_path)
    print('====================开始重命名PT图片===========================\n')
    align_ct_pt(ct_path=p_path)
    print('====================开始对PT图片插值===========================\n')
    get_align_dicom(ct_path=c_path, pt_path=p_path, pt_new_path=p_new_path)
    # 开始转换dcm到图片
    print('====================开始转换dcm到图片===========================\n')
    if not os.path.exists(c_jpg_save_path):
        os.mkdir(c_jpg_save_path)
    if not os.path.exists(p_jpg_save_path):
        os.mkdir(p_jpg_save_path)
    trans_dcm_2_jpg(source_dcm_path=c_path, save_jpg_path=c_jpg_save_path, tag='ct')
    trans_dcm_2_jpg(source_dcm_path=p_new_path, save_jpg_path=p_jpg_save_path, tag='pt')
    root = Tk()
    tool = LabelTool(root)
    root.mainloop()
    finally_save(
        patient_code=patient_code, save_path=os.path.join(label_path, patient_code, 'ct'), # r'E:\SearchQA\for_dicom_mark\for_dicom_mark\labels\%s\ct' % patient_code,
        c_path=c_path, p_new_path=p_new_path, mark_result_path=mark_result_path)
