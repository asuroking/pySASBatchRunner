#-------------------------------------------------------------------------------
# Name:        pySASBatchRunner
# Purpose:     Batch Run SAS programs
#
# Author:      Jwang19
#
# Created:     12/07/2012
# Copyright:   (c) Jwang19 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import sys
import os
import datetime
import json
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

from callSASPrograms import callSASPrograms


def selectAllItemsData(listCtrl):
    "select all items data in given LISTCTRL::listCtrl"
    if listCtrl.GetItemCount():
        for i in range(listCtrl.GetItemCount()):
            #listCtrl.SetItemState(i,wx.LIST_STATE_SELECTED,wx.LIST_STATE_SELECTED) # from url http://wiki.wxpython.org/ListControls
            listCtrl.Select(i, on=1)

def getSelectedItemsData(listCtrl):
    """
    retrieve Selected Items Data from given LISTCTRL::listCtrl.
    """

    selection = {}

    if listCtrl.GetSelectedItemCount():
        index = listCtrl.GetFirstSelected()
        selection[index] = (listCtrl.GetItem(index).GetText(),listCtrl.GetItem(index, 1).GetText())

        while len(selection) != listCtrl.GetSelectedItemCount():
            index = listCtrl.GetNextSelected(index)
            selection[index] = (listCtrl.GetItem(index).GetText(),listCtrl.GetItem(index, 1).GetText())

    return selection


class SASListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
    "ListCtrl with AutoWidthMixin, the last column will auto adjust it's width"
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT)
        ListCtrlAutoWidthMixin.__init__(self)

        self.InsertColumn(0,"SAS Program", width=200)
        self.InsertColumn(1,"Date Modified")


class batchSASProgramRunnerFrame(wx.Frame):
    """
    the main frame for SAS Program Runner
    """

    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Batch SAS Programs Runner", size=(800,600))

        self.icon = wx.Icon("icon-sas.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(self.icon)

        #panel and sizers
        panel = wx.Panel(self, -1)
        fsizer = wx.BoxSizer(wx.VERTICAL)
        topsizer = wx.BoxSizer(wx.HORIZONTAL)
        listsizer = wx.BoxSizer(wx.HORIZONTAL)
        jobsizer = wx.BoxSizer(wx.VERTICAL)
        bottomsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        bottomsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        bottomsizer3 = wx.BoxSizer(wx.HORIZONTAL)
        bottomsizer4 = wx.BoxSizer(wx.VERTICAL)
        bottomsizer5 = wx.BoxSizer(wx.HORIZONTAL)

        #Top line, input SAS Programs folder.
        txtctrl_inputdir = wx.TextCtrl(panel, -1, "input SAS Program folder.")
        #txtctrl_inputdir.Enabled = False
        btn_browsedir = wx.Button(panel, -1, "Browse Dir...")
        self.Bind(wx.EVT_BUTTON, self.OnBrowseDir, btn_browsedir)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnCheckInputDir, txtctrl_inputdir)
        self.Bind(wx.EVT_TEXT, self.OnAddPgmToList, txtctrl_inputdir)

        self.saspgmdir = txtctrl_inputdir
        self.inputdir_text = txtctrl_inputdir.GetValue()

        topsizer.Add(btn_browsedir, proportion=0, flag=wx.LEFT, border=5)
        topsizer.Add(txtctrl_inputdir, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=5)


        #add to job queue, remove from job queue
        btn_addjobqueue = wx.Button(panel, -1, "Add Jobs")
        btn_addjobqueue_all = wx.Button(panel, -1, "Add All Jobs")
        btn_deljobqueue = wx.Button(panel, -1, "Remove Jobs")
        btn_deljobqueue_all = wx.Button(panel, -1, "Remove All Jobs")
        self.Bind(wx.EVT_BUTTON, self.OnAddJob, btn_addjobqueue)
        self.Bind(wx.EVT_BUTTON, self.OnAddJobAll, btn_addjobqueue_all)
        self.Bind(wx.EVT_BUTTON, self.OnDelJob, btn_deljobqueue)
        self.Bind(wx.EVT_BUTTON, self.OnDelJobAll, btn_deljobqueue_all)

        jobsizer.Add(btn_addjobqueue, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)
        jobsizer.Add(btn_addjobqueue_all, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)
        jobsizer.Add(btn_deljobqueue, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)
        jobsizer.Add(btn_deljobqueue_all, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)


        #move job queue, up/down
        btn_jobqueue_uptop = wx.Button(panel, -1, "Move Top")
        btn_jobqueue_uptop.Enabled = False
        btn_jobqueue_up = wx.Button(panel, -1, "Move Up")
        btn_jobqueue_up.Enabled = False
        btn_jobqueue_down = wx.Button(panel, -1, "Move Down")
        btn_jobqueue_down.Enabled = False
        btn_jobqueue_downbottom = wx.Button(panel, -1, "Move Bottom")
        btn_jobqueue_downbottom.Enabled = False
        self.Bind(wx.EVT_BUTTON, self.OnJobUptop, btn_jobqueue_uptop)
        self.Bind(wx.EVT_BUTTON, self.OnJobUp, btn_jobqueue_up)
        self.Bind(wx.EVT_BUTTON, self.OnJobDown, btn_jobqueue_down)
        self.Bind(wx.EVT_BUTTON, self.OnJobDownBottom, btn_jobqueue_downbottom)

        jobsizer.Add(wx.StaticLine(panel,-1), proportion=0, flag=wx.EXPAND, border=5)
        jobsizer.Add(btn_jobqueue_uptop, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)
        jobsizer.Add(btn_jobqueue_up, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)
        jobsizer.Add(btn_jobqueue_down, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)
        jobsizer.Add(btn_jobqueue_downbottom, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)


        #save job queue, load job queue
        self.btn_jobqueue_save = wx.Button(panel, -1, "Save Job...")
        self.btn_jobqueue_save.Enabled = False
        self.btn_jobqueue_load = wx.Button(panel, -1, "Load Job...")
        self.Bind(wx.EVT_BUTTON, self.OnJobSave, self.btn_jobqueue_save)
        self.Bind(wx.EVT_BUTTON, self.OnJobLoad, self.btn_jobqueue_load)

        jobsizer.Add(wx.StaticLine(panel,-1), proportion=0, flag=wx.EXPAND, border=5)
        jobsizer.Add(self.btn_jobqueue_save, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)
        jobsizer.Add(self.btn_jobqueue_load, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)


        #left, right, list control, let user choose SAS Programs.
        self.list_input_pgm = SASListCtrl(panel)
        self.list_output_pgm = SASListCtrl(panel)

        listsizer.Add(self.list_input_pgm, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=5)
        listsizer.Add(jobsizer, proportion=0, flag=wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ALL, border=5)
        listsizer.Add(self.list_output_pgm, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=5)


        #SAS Log, Output folder
        btn_logto = wx.Button(panel, -1, "Log...")
        txtctrl_logto = wx.TextCtrl(panel, -1, "output SAS Log folder.")
        #txtctrl_logto.Enabled = False
        self.Bind(wx.EVT_BUTTON, self.OnBrowseLog, btn_logto)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnCheckLogDir, txtctrl_logto)
        self.saslogdir = txtctrl_logto
        self.logdir_text = txtctrl_logto.GetValue()

        bottomsizer1.Add(btn_logto, proportion=0, flag=wx.LEFT, border=5)
        bottomsizer1.Add(txtctrl_logto, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=5)


        btn_listto = wx.Button(panel, -1, "List...")
        txtctrl_listto = wx.TextCtrl(panel, -1, "onput SAS Output folder.")
        #txtctrl_listto.Enabled = False
        self.Bind(wx.EVT_BUTTON, self.OnBrowseList, btn_listto)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnCheckListDir, btn_listto)
        self.saslistdir = txtctrl_listto
        self.listdir_text = txtctrl_listto.GetValue()

        bottomsizer2.Add(btn_listto, proportion=0, flag=wx.LEFT, border=5)
        bottomsizer2.Add(txtctrl_listto, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=5)


        bottomsizer4.Add(bottomsizer1, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)
        bottomsizer4.Add(bottomsizer2, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)

        #Batch Run button
        btn_batchun = wx.Button(panel, -1, "Batch Run")
        self.Bind(wx.EVT_BUTTON, self.OnBatchRun, btn_batchun)

        bottomsizer3.Add(btn_batchun, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=5)


        bottomsizer5.Add(bottomsizer4, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, border=5)
        bottomsizer5.Add(bottomsizer3, proportion=0, flag=wx.LEFT|wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, border=5)


        #add all controls together
        fsizer.Add((-1,5))
        fsizer.Add(topsizer, proportion=0, flag=wx.LEFT|wx.EXPAND, border=5)
        fsizer.Add((-1,5))
        fsizer.Add(wx.StaticLine(panel,-1), 0, wx.ALIGN_CENTER|wx.EXPAND, border=5)
        fsizer.Add((-1,5))
        fsizer.Add(listsizer, proportion=1, flag=wx.LEFT|wx.EXPAND, border=5)
        fsizer.Add((-1,5))
        fsizer.Add(wx.StaticLine(panel,-1), 0, wx.ALIGN_CENTER|wx.EXPAND, border=5)
        fsizer.Add((-1,5))
        fsizer.Add(bottomsizer5, proportion=0, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=5)
        fsizer.Add((-1,5))

        panel.SetSizer(fsizer)


    def OnJobSave(self, event):
        "save all current config to a external JSON file"
        myconfig = {}

        wildcard = "pySASBatchRunner Job (*.json)|*.json"
        dlg = wx.FileDialog(
              self, message="Save Jobqueue as JSON file...", defaultDir=self.saspgmdir.GetValue(),
              defaultFile="",wildcard=wildcard, style=wx.SAVE
              )

        dlg.SetFilterIndex(0)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()

            fmyconfig = file(path,'w');

            myconfig["browse_dir"] = self.saspgmdir.GetValue()
            myconfig["log_dir"] = self.saslogdir.GetValue()
            myconfig["list_dir"] = self.saslistdir.GetValue()

            selectAllItemsData(self.list_output_pgm)
            selectedItemData = getSelectedItemsData(self.list_output_pgm)
            myconfig["selected_pgms"] = selectedItemData

            #print "Saving jobs to external JSON file ..."
            fmyconfig.write(json.dumps(myconfig, sort_keys=False, indent=4, encoding='utf-8'))
            fmyconfig.close

        dlg.Destroy()

    def OnJobLoad(self, event):
        myconfig = {}
        wildcard = "pySASBatchRunner Job (*.json)|*.json"

        dlg = wx.FileDialog(
              self, message="Load Jobqueue from a JSON file...", defaultDir=self.saspgmdir.GetValue(),
              defaultFile="",wildcard=wildcard, style=wx.OPEN|wx.CHANGE_DIR
              )

        dlg.SetFilterIndex(0)

        if dlg.ShowModal() == wx.ID_OK:
            #clear original item data in left/right ListCtrl
            self.list_input_pgm.DeleteAllItems()
            self.list_output_pgm.DeleteAllItems()

            path = dlg.GetPath()
            fmyconfig = file(path,'rb');

            myconfig = json.load(fmyconfig)

            self.saspgmdir.SetValue(myconfig['browse_dir'])
            self.saslogdir.SetValue(myconfig['log_dir'])
            self.saslistdir.SetValue(myconfig['list_dir'])

            loadItemData = myconfig['selected_pgms']
            pgm_list = []
            if len(loadItemData):
                for indx, value in loadItemData.iteritems():
                    lastindex =self.list_output_pgm.GetItemCount()
                    self.list_output_pgm.InsertStringItem(lastindex, value[0])
                    self.list_output_pgm.SetStringItem(lastindex, 1, value[1])
                    pgm_list.append(value[0])

                if self.list_output_pgm.GetItemCount():
                    self.btn_jobqueue_save.Enabled = True

                #remove those already in left Ctrl
                l_cnt = self.list_input_pgm.GetItemCount()
                l_r = range(l_cnt)
                for i in range(l_cnt):
                    idx = l_r.pop()
                    if self.list_input_pgm.GetItemText(idx) in pgm_list:
                        self.list_input_pgm.DeleteItem(idx)

        dlg.Destroy()

    def OnAddJob(self, event):

        selectedItemData = getSelectedItemsData(self.list_input_pgm)

        if len(selectedItemData):
            for indx, value in selectedItemData.iteritems():
                lastindex =self.list_output_pgm.GetItemCount()
                self.list_output_pgm.InsertStringItem(lastindex, value[0])
                self.list_output_pgm.SetStringItem(lastindex, 1, value[1])

            #delete selected item from left ListCtrl
            todelete = selectedItemData.keys()
            while len(todelete):
                rr = todelete.pop()
                self.list_input_pgm.DeleteItem(rr)

        if self.list_output_pgm.GetItemCount():
            self.btn_jobqueue_save.Enabled = True
        else:
            self.btn_jobqueue_save.Enabled = False


    def OnAddJobAll(self, event):
        if self.list_input_pgm.GetItemCount():
            #select all items in left ListCtrl
            selectAllItemsData(self.list_input_pgm)

            selectedItemData = getSelectedItemsData(self.list_input_pgm)

            if len(selectedItemData):
                for indx, value in selectedItemData.iteritems():
                    lastindex =self.list_output_pgm.GetItemCount()
                    self.list_output_pgm.InsertStringItem(lastindex, value[0])
                    self.list_output_pgm.SetStringItem(lastindex, 1, value[1])

                #delete selected item from left ListCtrl
                self.list_input_pgm.DeleteAllItems()
                """
                todelete = selectedItemData.keys()
                while len(todelete):
                    rr = todelete.pop()
                    self.list_input_pgm.DeleteItem(rr)
                """

            if self.list_output_pgm.GetItemCount():
                self.btn_jobqueue_save.Enabled = True
            else:
                self.btn_jobqueue_save.Enabled = False

    def OnDelJob(self, event):

        selectedItemData = getSelectedItemsData(self.list_output_pgm)

        if len(selectedItemData):
            for indx, value in selectedItemData.iteritems():
                lastindex =self.list_input_pgm.GetItemCount()
                self.list_input_pgm.InsertStringItem(lastindex, value[0])
                self.list_input_pgm.SetStringItem(lastindex, 1, value[1])

            #delete selected item from right ListCtrl
            todelete = selectedItemData.keys()
            while len(todelete):
                rr = todelete.pop()
                self.list_output_pgm.DeleteItem(rr)

        if self.list_output_pgm.GetItemCount():
            self.btn_jobqueue_save.Enabled = True
        else:
            self.btn_jobqueue_save.Enabled = False

    def OnDelJobAll(self, event):
        if self.list_output_pgm.GetItemCount():
            #select all items in right ListCtrl
            selectAllItemsData(self.list_output_pgm)

            selectedItemData = getSelectedItemsData(self.list_output_pgm)

            if len(selectedItemData):
                for indx, value in selectedItemData.iteritems():
                    lastindex =self.list_input_pgm.GetItemCount()
                    self.list_input_pgm.InsertStringItem(lastindex, value[0])
                    self.list_input_pgm.SetStringItem(lastindex, 1, value[1])

                #delete selected item from right ListCtrl
                self.list_output_pgm.DeleteAllItems()
                """
                todelete = selectedItemData.keys()
                while len(todelete):
                    rr = todelete.pop()
                    self.list_output_pgm.DeleteItem(rr)
                """

            if self.list_output_pgm.GetItemCount():
                self.btn_jobqueue_save.Enabled = True
            else:
                self.btn_jobqueue_save.Enabled = False

    def OnJobUptop(self, event):
        pass

    def OnJobUp(self, event):
        pass

    def OnJobDown(self, event):
        pass

    def OnJobDownBottom(self, event):
        pass

    def OnCheckInputDir(self, event):
        new_inputdir_text = self.saspgmdir.GetValue()
        print new_inputdir_text
        if new_inputdir_text != self.inputdir_text:
            if os.path.exists(new_inputdir_text):
                self.inputdir_text = new_inputdir_text
                print new_inputdir_text
                self._AddPgmToList()
            else:
                #new entered folder not exist, set it back to original value
                self.saspgmdir.SetValue(self.inputdir_text)

    def OnCheckListDir(self, event):
        new_listdir_text = self.saslistdir.GetValue()
        print new_listdir_text
        if new_listdir_text != self.listdir_text:
            if os.path.exists(new_listdir_text):
                self.listdir_text = new_listdir_text
            else:
                #new entered folder not exist, set it back to original value
                self.saslistdir.SetValue(self.listdir_text)

    def OnCheckLogDir(self, event):
        new_logdir_text = self.saslogdir.GetValue()
        print new_logdir_text
        if new_logdir_text != self.logdir_text:
            if os.path.exists(new_logdir_text):
                self.logdir_text = new_logdir_text
            else:
                #new entered folder not exist, set it back to original value
                self.saslogdir.SetValue(self.logdir_text)

    def _AddPgmToList(self):
        mySASPgmList = []
        #list_cnt = self.list_input_pgm.GetItemCount()
        self.list_input_pgm.DeleteAllItems()

        for filename in os.listdir(self.saspgmdir.GetValue()):
            #print filename
            if filename.split(".")[-1].lower() == "sas":
                filefullname = self.saspgmdir.GetValue() + "/" + filename
                t = os.path.getmtime(filefullname)
                filedate = datetime.datetime.fromtimestamp(t)
                filedates = filedate.strftime('%Y-%m-%d-%H:%M:%S')
                mySASPgmList.append([filename,filedates])

        if len(mySASPgmList):
            for index, SASPgm in enumerate(mySASPgmList):
                self.list_input_pgm.InsertStringItem(index,SASPgm[0])
                self.list_input_pgm.SetStringItem(index,1,SASPgm[1])


    def OnAddPgmToList(self, event):
        self._AddPgmToList()

    def OnBatchRun(self, event):
        # add all program to list saspgmlist [(pgm, log, list),(pgm, log, list)]
        saspgmlist = []

        _pgm_dir = self.saspgmdir.GetValue()
        log_dir = self.saslogdir.GetValue()
        list_dir = self.saslistdir.GetValue()

        # changing current work directory
        os.chdir(_pgm_dir)

        if self.list_output_pgm.GetItemCount():
            for i in range(self.list_output_pgm.GetItemCount()):
                pgm = self.list_output_pgm.GetItemText(i)

                pgm_fullpath = _pgm_dir + "\\" + pgm

                saspgmlist.append([pgm_fullpath, log_dir, list_dir])

        if len(saspgmlist):
            callSASPrograms(saspgmlist)

    def OnBrowseDir(self, event):
        _defaultdir = os.getcwd()
        if self.saspgmdir.GetValue() != "input SAS Program folder." and len(self.saspgmdir.GetValue()):
            _defaultdir = self.saspgmdir.GetValue()

        dlg = wx.DirDialog(self, "Choose a directory:", defaultPath=_defaultdir, style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            self.saspgmdir.SetValue(dlg.GetPath())
            self.saslogdir.SetValue(dlg.GetPath())
            self.saslistdir.SetValue(dlg.GetPath())

            self.inputdir_text = dlg.GetPath()

            os.chdir(dlg.GetPath())

            return dlg.GetPath()


        dlg.Destroy()


    def OnBrowseLog(self, event):
        dlg = wx.DirDialog(self, "Choose a directory:", defaultPath=os.getcwd(), style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            self.saslogdir.SetValue(dlg.GetPath())

            self.logdir_text = dlg.GetPath()

            return dlg.GetPath()

        dlg.Destroy()

    def OnBrowseList(self, event):
        dlg = wx.DirDialog(self, "Choose a directory:", defaultPath=os.getcwd(), style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            self.saslistdir.SetValue(dlg.GetPath())

            self.listdir_text = dlg.GetPath()

            return dlg.GetPath()

        dlg.Destroy()

    def OnCloseWindow(self, event):
        self.Destroy()


def main():
    app = wx.PySimpleApp()
    batchSASProgramRunnerFrame().Show()
    app.MainLoop()


if __name__ == '__main__':
    main()

