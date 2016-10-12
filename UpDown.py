import Utils
import Model
import Sprints
import wx
import re
import wx.grid		as gridlib
import wx.lib.mixins.grid as gae

notNumberRE = re.compile( u'[^0-9]' )

# Columns for the table.
BibExistingPoints = 0
ValExistingPoints = 1

BibUpDown = 3
ValUpDown = 4

BibStatus = 6
ValStatus = 7

ValFinish = 9
BibFinish = 10

EmptyCols = [2, 5, 8]

class UpDownEditor(gridlib.PyGridCellEditor):
	Empty = u''
	
	def __init__(self):
		self._tc = None
		self.startValue = self.Empty
		gridlib.PyGridCellEditor.__init__(self)
		
	def Create( self, parent, id = wx.ID_ANY, eventHandler = None ):
		self._tc = wx.SpinCtrl(parent, id, style = wx.TE_PROCESS_ENTER, min=-160, max=160)
		self.SetControl( self._tc )
		if eventHandler:
			self._tc.PushEventHandler( eventHandler )
	
	def SetSize( self, rect ):
		self._tc.SetDimensions(rect.x, rect.y, rect.width+2, rect.height+2, wx.SIZE_ALLOW_MINUS_ONE )
	
	def BeginEdit( self, row, col, grid ):
		self.startValue = grid.GetTable().GetValue(row, col).strip()
		v = self.startValue
		self._tc.SetValue( int(v or u'0') )
		self._tc.SetFocus()
		
	def EndEdit( self, row, col, grid, value = None ):
		changed = False
		v = self._tc.GetValue()
		if v == 0:
			v = u''
		elif v > 0:
			v = u'+' + unicode(v)
		else:
			v = unicode(v)
		
		if v != self.startValue:
			changed = True
			grid.GetTable().SetValue( row, col, v )
		
		self.startValue = self.Empty
		self._tc.SetValue( 0 )
		return v if changed else None
		
	def Reset( self ):
		self._tc.SetValue( self.startValue )
		
	def Clone( self ):
		return UpDownEditor()

class UpDownGrid( gridlib.Grid, gae.GridAutoEditMixin ):
	def __init__( self, parent, id=wx.ID_ANY, style=0 ):
		gridlib.Grid.__init__( self, parent, id=id, style=style )
		gae.GridAutoEditMixin.__init__(self)
		
		self.cBibExistingPoints = 0
		self.cExistingPoints = 1
		
		self.cBibLaps = 3
		self.cLaps = 4
		
		self.cBibStatus = 6
		self.cStatus = 7
		
		self.cBibFinishOrder = 10
		self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

	def OnKeyDown(self, event):
		if event.GetKeyCode() != wx.WXK_RETURN:
			event.Skip()
			return
		if event.ControlDown():   # the edit control needs this key
			event.Skip()
			return
		self.DisableCellEditControl()
		
		r = self.GetGridCursorRow()
		c = self.GetGridCursorCol()
		
		# Move the cursor to the next logical column.
		if c in (self.cBibExistingPoints, self.cBibLaps, self.cBibStatus):
			self.SetGridCursor( r, c+1 )
		elif c in (self.cExistingPoints, self.cLaps, self.cStatus):
			self.SetGridCursor( r+1, c-1 )
		elif c == self.cBibFinishOrder:
			self.SetGridCursor( r+1, c )
		
class UpDown( wx.Panel ):
	def __init__( self, parent, id = wx.ID_ANY ):
		super(UpDown, self).__init__( parent, id, style=wx.BORDER_SUNKEN)
		self.SetBackgroundColour( wx.WHITE )
		
		self.inCellChange = False

		self.hbs = wx.BoxSizer(wx.HORIZONTAL)

		self.gridUpDown = UpDownGrid( self )
		labels = [u'Bib', u'Existing\nPoints', u' ', u'Bib', u'Laps\n+/-', u' ', u'Bib', u'Status', u' ', u'Finish\nOrder', u'Bib', ]
		self.gridUpDown.CreateGrid( 200, len(labels) )
		
		for col, colName in enumerate(labels):
			self.gridUpDown.SetColLabelValue( col, colName )
			
			attr = gridlib.GridCellAttr()
						
			if col in (BibUpDown, ValUpDown, BibFinish, BibStatus, BibExistingPoints, ValExistingPoints):
				attr.SetEditor( gridlib.GridCellNumberEditor() )
				attr.SetAlignment( wx.ALIGN_RIGHT, wx.ALIGN_CENTRE )
			
			elif col == ValStatus:
				attr.SetEditor( gridlib.GridCellChoiceEditor([' '] + Model.Rider.statusNames[1:], False) )
				attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_CENTRE )
			
			else:
				attr.SetReadOnly()
				attr.SetAlignment( wx.ALIGN_RIGHT, wx.ALIGN_CENTRE )
				
			if col in EmptyCols:
				attr.SetBackgroundColour( self.gridUpDown.GetLabelBackgroundColour() )
				
			self.gridUpDown.SetColAttr( col, attr )

		self.gridUpDown.SetRowLabelSize( 0 )
		
		self.gridUpDown.EnableDragColSize( False )
		self.gridUpDown.EnableDragRowSize( False )
		self.gridUpDown.AutoSize()
		
		try:
			mainWin = Utils.getMainWin()
			widestCol = mainWin.sprints.gridWorksheet.GetColSize( 0 )
		except:
			widestCol = 64
		for i in xrange( self.gridUpDown.GetNumberCols() ):
			self.gridUpDown.SetColSize( i, max(widestCol, self.gridUpDown.GetColSize(i)) )

		for col in EmptyCols:
			self.gridUpDown.SetColSize( col, 16 )
		
		self.Bind(gridlib.EVT_GRID_CELL_CHANGE, self.onCellChange)
		self.Bind(gridlib.EVT_GRID_SELECT_CELL, self.onCellEnableEdit)
		self.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.onLabelClick)
		self.Bind(gridlib.EVT_GRID_EDITOR_CREATED, self.onGridEditorCreated)
		self.hbs.Add( self.gridUpDown, 1, wx.GROW|wx.ALL, border = 4 )
		
		self.gridUpDown.AutoSizeColumn( 9 )
		
		self.SetSizer(self.hbs)
		self.hbs.SetSizeHints(self)

	def onLeaveWindow( self, event ):
		pass
		
	def onGridEditorCreated( self, event ):
		editor = event.GetControl()
		editor.Bind( wx.EVT_KILL_FOCUS, self.onKillFocus )
		event.Skip()
		
	def onKillFocus( self, event ):
		grid = event.GetEventObject().GetGrandParent()
		grid.SaveEditControlValue()
		grid.HideCellEditControl()
		event.Skip()
		
	def onLabelClick( self, event=None ):
		self.gridUpDown.DisableCellEditControl()
		wx.CallAfter( self.refresh )
		event.Skip()
		
	def onCellChange( self, event ):
		r = event.GetRow()
		c = event.GetCol()
		value = self.gridUpDown.GetCellValue(r, c)
		value = value.strip()
		if c == ValUpDown:
			try:
				value = u'{:+d}'.format(int(value))
			except:
				pass
		elif c != ValStatus:
			value = notNumberRE.sub( u'', value )
			if value in (u'-0', u'0', u'+0'):
				value = u''

		self.gridUpDown.SetCellValue(r, c, value)
		self.commit()
		Utils.refreshResults()
	
	def onCellEnableEdit( self, event ):
		if event.GetCol() == ValStatus:
			wx.CallAfter( self.gridUpDown.EnableCellEditControl )
		event.Skip()
	
	def clear( self ):
		for r in xrange( self.gridUpDown.GetNumberRows() ):
			for c in xrange( self.gridUpDown.GetNumberCols() ):
				self.gridUpDown.SetCellValue( r, c, u'' )
		
	def refresh( self ):
		self.clear()
		race = Model.race
		if not race:
			return
			
		for r, (num, updown) in enumerate(race.getUpDown()):
			self.gridUpDown.SetCellValue( r, BibUpDown, unicode(num) )
			self.gridUpDown.SetCellValue( r, ValUpDown, u'{:+d}'.format(updown) )
		
		for r, (num, s) in enumerate(race.getStatus()):
			self.gridUpDown.SetCellValue( r, BibStatus, unicode(num) )
			self.gridUpDown.SetCellValue( r, ValStatus, Model.Rider.statusNames[s] )
			
		for r in xrange( self.gridUpDown.GetNumberRows() ):
			self.gridUpDown.SetCellValue( r, ValFinish, unicode(r+1) )
			
		orderNum = {order: num for num, order in race.getFinishOrder()}
		for num, order in race.getFinishOrder():
			self.gridUpDown.SetCellValue( order-1, BibFinish, unicode(num) )
		
		for r, (num, p) in enumerate(race.getExistingPoints()):
			self.gridUpDown.SetCellValue( r, BibExistingPoints, unicode(num) )
			self.gridUpDown.SetCellValue( r, ValExistingPoints, unicode(p) )
			
	def commit( self ):
		race = Model.race
		if not race:
			return
		
		lastFinishVal = 0
		existingPoints = {}
		updowns = {}
		finishOrder = {}
		status = {}
		statusIndex = dict( (n, i) for i, n in enumerate(Model.Rider.statusNames) )
		for r in xrange(self.gridUpDown.GetNumberRows()):
			try:
				bib = int(self.gridUpDown.GetCellValue(r, BibExistingPoints), 10)
				points = int(self.gridUpDown.GetCellValue(r, ValExistingPoints), 10)
				if bib:
					existingPoints[bib] = points
			except ValueError:
				pass
		
			try:
				bib = int(self.gridUpDown.GetCellValue(r, BibUpDown), 10)
				ud = int(self.gridUpDown.GetCellValue(r, ValUpDown), 10)
				if bib:
					updowns[bib] = updowns.get(bib, 0) + ud
			except ValueError:
				pass
					
			try:
				bib = int(self.gridUpDown.GetCellValue(r, BibStatus), 10)
				i = statusIndex[self.gridUpDown.GetCellValue(r, ValStatus)]
				status[bib] = i
			except (ValueError, KeyError):
				pass
			
			try:
				bib = int(self.gridUpDown.GetCellValue(r, BibFinish), 10)
				if bib:
					finishStr = self.gridUpDown.GetCellValue(r, ValFinish).strip()
					if finishStr:
						finishVal = int(finishStr)
						lastFinishVal = finishVal
					else:
						finishVal = lastFinishVal + 1
					finishOrder[bib] = finishVal
					lastFinishVal = finishVal
			except ValueError:
				pass

		race.setExistingPoints( existingPoints )
		race.setUpDowns( updowns )
		race.setStatus( status )
		race.setFinishOrder( finishOrder )
	
if __name__ == '__main__':
	app = wx.App( False )
	mainWin = wx.Frame(None,title="PointsRaceMgr", size=(600,400))
	Model.setRace( Model.Race() )
	Model.getRace()._populate()
	updown = UpDown(mainWin)
	updown.refresh()
	mainWin.Show()
	app.MainLoop()
