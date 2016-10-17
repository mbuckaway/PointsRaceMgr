import wx
import os
import math
import datetime
import Utils
import Model

class GrowTable( object ):
	bold, alignLeft, alignCentre, alignRight, alignTop, alignMiddle, alignBottom = [1<<i for i in xrange(7)]
	alignCenter = alignCentre
	attrDefault = alignRight|alignTop
	
	def __init__( self, alignHorizontal=alignCentre, alignVertical=alignCentre, cellBorder=True ):
		self.alignHorizontal = alignHorizontal
		self.alignVertical = alignVertical
		self.cellBorder = cellBorder
		self.clear()
	
	def clear( self ):
		self.table = []
		self.colWidths = []
		self.rowHeights = []
		self.vLines = []
		self.hLines = []
		self.width = None
		self.height = None
	
	def fromGrid( self, grid, horizontalGridlines=True, verticalGridlines=False ):
		self.clear()
		mapHorizontal = {
			wx.ALIGN_LEFT: self.alignLeft,
			wx.ALIGN_RIGHT: self.alignRight,
			wx.ALIGN_CENTER: self.alignCenter,
		}
		mapVertical = {
			wx.ALIGN_TOP: self.alignTop,
			wx.ALIGN_BOTTOM: self.alignBottom,
			wx.ALIGN_CENTER: self.alignMiddle,
		}
		rowLabel = 0
		colLabel = 0
		if grid.GetRowLabelSize() > 0:
			colLabel = 1
		if grid.GetColLabelSize() > 0 and grid.GetNumberCols():
			maxNewLines = max(grid.GetColLabelValue(c).count('\n') for c in xrange(grid.GetNumberCols()))
			def fixNewLines( v ):
				d = maxNewLines - v.count(u'\n')
				return v if d == 0 else u'\n'*d + v
			for c in xrange(grid.GetNumberCols()):
				self.set( 0, c+colLabel, fixNewLines(grid.GetColLabelValue(c)), self.bold )
			rowLabel = 1
		if colLabel > 0:
			for r in xrange(grid.GetNumberRows()):
				self.set( r+rowLabel, 0, grid.GetRowLabelValue(r), self.bold )
		
		def isNumeric( v ):
			if not v:
				return True
			try:
				f = float(v)
				return True
			except:
				return False
		
		allNumericCol = set( c for c in xrange(grid.GetNumberCols()) if all(isNumeric(grid.GetCellValue(r, c)) for r in xrange(grid.GetNumberRows())) )
		for r in xrange(grid.GetNumberRows()):
			for c in xrange(grid.GetNumberCols()):
				v = grid.GetCellValue( r, c )
				if not v:
					continue
				aHoriz, aVert = grid.GetCellAlignment(r, c)
				if c in allNumericCol:
					aHoriz = wx.ALIGN_RIGHT
				self.set( r+rowLabel, c+colLabel, v, mapHorizontal.get(aHoriz, self.alignLeft) | mapVertical.get(aVert, self.alignTop) )
			
		numCols, numRow = self.getNumberCols(), self.getNumberRows()
		if horizontalGridlines:
			if rowLabel > 0:
				self.hLine( 1, 0, numCols, True )
			for r in xrange(rowLabel, grid.GetNumberRows()+1):
				self.hLine( r+rowLabel, 0, numCols )
		if verticalGridlines:
			self.vLine( 0, 0, numRows )
			if colLabel > 0:
				self.hLine( 1, 0, numRows, True )
			for c in xrange(colLabel+1, grid.GetNumberCols()+1):
				self.hLine( c+colLabel, 0, numRows )
		
	def set( self, row, col, value, attr=attrDefault ):
		self.table += [[] for i in xrange(max(0, row+1 - len(self.table)))]
		self.table[row] += [(u'', self.attrDefault) for i in xrange(max(0, col+1 - len(self.table[row])))]
		self.table[row][col] = (value, attr)
		return row, col
		
	def vLine( self, col, rowStart, rowEnd, thick = False ):
		# Drawn on the left of the col.
		self.vLines.append( (col, rowStart, rowEnd, thick) )
		
	def hLine( self, row, colStart, colEnd, thick = False ):
		# Drawn on the top of the row.
		self.hLines.append( (row, colStart, colEnd, thick) )
		
	def getNumberCols( self ):
		return max(len(r) for r in self.table)
		
	def getNumberRows( self ):
		return len(self.table)
		
	def getFonts( self, fontSize ):
		font = wx.FontFromPixelSize( wx.Size(0,fontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
		fontBold = wx.FontFromPixelSize( wx.Size(0,fontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_BOLD )
		return font, fontBold
		
	def getCellBorder( self, fontSize ):
		return max(1, fontSize // 5) if self.cellBorder else 0
		
	def getSize( self, dc, fontSize ):
		font, fontBold = self.getFonts( fontSize )
		cellBorderX2 = self.getCellBorder( fontSize ) * 2
		self.colWidths = [0] * self.getNumberCols()
		self.rowHeights = [0] * self.getNumberRows()
		for row, r in enumerate(self.table):
			for col, (value, attr) in enumerate(r):
				vWidth, vHeight, lineHeight = dc.GetMultiLineTextExtent(value, fontBold if attr&self.bold else font)
				self.colWidths[col] = max(self.colWidths[col], vWidth + cellBorderX2)
				self.rowHeights[row] = max(self.rowHeights[row], vHeight + cellBorderX2)
		return sum( self.colWidths ), sum( self.rowHeights )
	
	def drawTextToFit( self, dc, text, x, y, width, height, attr, font=None ):
		if font and font != dc.GetFont():
			dc.SetFont( font )
		fontSize = dc.GetFont().GetPixelSize()[1]
		cellBorder = self.getCellBorder( fontSize )
		tWidth, tHeight, lineHeight = dc.GetMultiLineTextExtent(text, dc.GetFont())
		xLeft = x + cellBorder
		xRight = x + width - cellBorder
		
		if attr&self.alignMiddle:
			yTop = y + (height - tHeight) // 2
		elif attr&self.alignBottom:
			yTop = y + height - cellBorder - tHeight
		else:
			yTop = y + cellBorder
		
		for line in text.split( '\n' ):
			if attr & self.alignRight:
				dc.DrawText( line, xRight - dc.GetTextExtent(line)[0], yTop )
			elif attr & self.alignLeft:
				dc.DrawText( line, xLeft, yTop )
			else:
				dc.DrawText( line, x + (width - dc.GetTextExtent(line)[0]) // 2, yTop )
			yTop += lineHeight
			
	def setPen( self, dc, thick = False ):
		if not self.penThin:
			self.penThin = wx.Pen( wx.BLACK, 1, wx.SOLID )
			fontheight = dc.GetFont().GetPixelSize()[1]
			cellBorder = self.getCellBorder( fontheight )
			width = cellBorder / 2
			self.penThick = wx.Pen( wx.BLACK, width, wx.SOLID )
		newPen = self.penThick if thick else self.penThin
		if newPen != dc.GetPen():
			dc.SetPen( newPen )
	
	def drawToFitDC( self, dc, x, y, width, height ):
		self.penThin = None
		self.penThick = None
		
		fontSizeLeft, fontSizeRight = 2, 512
		for i in xrange(20):
			fontSize = (fontSizeLeft + fontSizeRight) // 2
			tWidth, tHeight = self.getSize( dc, fontSize )
			if tWidth < width and tHeight < height:
				fontSizeLeft = fontSize
			else:
				fontSizeRight = fontSize
			if fontSizeLeft == fontSizeRight:
				break
		
		fontSize = fontSizeLeft
		tWidth, tHeight = self.getSize( dc, fontSize )
		self.width, self.height = tWidth, tHeight
		
		# Align the entire table in the space.
		if self.alignHorizontal == self.alignCentre:
			x += (width - tWidth) // 2
		elif self.alignHorizontal == self.alignRight:
			x += width - tWidth

		if self.alignVertical == self.alignCentre:
			y += (height - tHeight) // 2
		elif self.alignVertical == self.alignBottom:
			y += height - tHeight
			
		self.x = x
		self.y = y

		font, fontBold = self.getFonts( fontSize )
		yTop = y
		for row, r in enumerate(self.table):
			xLeft = x
			for col, (value, attr) in enumerate(r):
				self.drawTextToFit( dc, value, xLeft, yTop, self.colWidths[col], self.rowHeights[row], attr, fontBold if attr&self.bold else font )
				xLeft += self.colWidths[col]
			yTop += self.rowHeights[row]
		
		# Draw the horizontal and vertical lines.
		# Lines are drawn on the left/top of the col/row.
		rowHeightSum = [y]
		for h in self.rowHeights:
			rowHeightSum.append( rowHeightSum[-1] + h )
		for i in xrange(50):
			rowHeightSum.append( rowHeightSum[-1] + rowHeightSum[-1] - rowHeightSum[-2] )
		
		colWidthSum = [x]
		for w in self.colWidths:
			colWidthSum.append( colWidthSum[-1] + w )
		
		curThick = None
		for col, rowStart, rowEnd, thick in self.vLines:
			if curThick != thick:
				self.setPen( dc, thick )
				curThick = thick
			colWidthSum[col]
			rowHeightSum[rowStart]
			colWidthSum[col]
			rowHeightSum[rowEnd]
			dc.DrawLine( colWidthSum[col], rowHeightSum[rowStart], colWidthSum[col], rowHeightSum[rowEnd] )
	
		curThick = None
		for row, colStart, colEnd, thick in self.hLines:
			if curThick != thick:
				self.setPen( dc, thick )
				curThick = thick
			dc.DrawLine( colWidthSum[colStart], rowHeightSum[row], colWidthSum[colEnd], rowHeightSum[row] )

	def toExcel( self, wx, rowStart=0, colStart=0 ):
		pass
	
	def toPDF( self, pdf, x, y, width, height ):
		pass
	
	def toHtmlTable( self ):
		pass
	
def ToPrintout( dc ):
	race = Model.race
	scoreSheet = Utils.getMainWin()
	
	#---------------------------------------------------------------------------------------
	# Format on the page.
	(widthPix, heightPix) = dc.GetSizeTuple()
	
	# Get a reasonable border.
	borderPix = max(widthPix, heightPix) / 25
	
	widthFieldPix = widthPix - borderPix * 2
	heightFieldPix = heightPix - borderPix * 2
	
	xPix = borderPix
	yPix = borderPix

	# Race Information
	xLeft = xPix
	yTop = yPix
	
	gt = GrowTable(alignHorizontal=GrowTable.alignLeft, alignVertical=GrowTable.alignTop, cellBorder=False)
	titleAttr = GrowTable.bold | GrowTable.alignLeft
	rowCur = 0
	rowCur = gt.set( rowCur, 0, race.name, titleAttr )[0] + 1
	rowCur = gt.set( rowCur, 0, race.category, titleAttr )[0] + 1
	rowCur = gt.set( rowCur, 0, u'{} Laps, {} Sprints, {} km'.format(race.laps, race.getNumSprints(), race.getDistance()), titleAttr )[0] + 1
	rowCur = gt.set( rowCur, 0, race.date.strftime('%Y-%m-%d'), titleAttr )[0] + 1
	
	if race.communique:
		rowCur = gt.set( rowCur, 0, u'Communiqu\u00E9: {}'.format(race.communique), GrowTable.alignRight )[0] + 1
	rowCur = gt.set( rowCur, 0, u'Approved by:________', GrowTable.alignRight )[0] + 1
	
	# Draw the title
	titleHeight = heightFieldPix * 0.15
	
	image = wx.Image( os.path.join(Utils.getImageFolder(), 'Sprint1.png'), wx.BITMAP_TYPE_PNG )
	imageWidth, imageHeight = image.GetWidth(), image.GetHeight()
	imageScale = float(titleHeight) / float(imageHeight)
	newImageWidth, newImageHeight = int(imageWidth * imageScale), int(imageHeight * imageScale)
	image.Rescale( newImageWidth, newImageHeight, wx.IMAGE_QUALITY_HIGH )
	dc.DrawBitmap( wx.BitmapFromImage(image), xLeft, yTop )
	del image
	newImageWidth += titleHeight / 10
	
	gt.drawToFitDC( dc, xLeft + newImageWidth, yTop, widthFieldPix - newImageWidth, titleHeight )
	yTop += titleHeight * 1.20
	
	# Collect all the sprint and worksheet results information.
	gt = GrowTable(GrowTable.alignCenter, GrowTable.alignTop)
	
	maxSprints = race.laps / race.sprintEvery
	
	gridPoints = scoreSheet.sprints.gridPoints
	gridSprint = scoreSheet.sprints.gridSprint
	
	colAdjust = {}
	colAdjust[gridPoints] = 1
	
	def makeTwoLines( s ):
		return '\n' + s if '\n' not in s else s
	
	# First get the sprint results.
	rowCur = 0
	colCur = 0
	for grid in [gridPoints, gridSprint]:
		for col in xrange(maxSprints if grid == gridSprint else grid.GetNumberCols() - colAdjust.get(grid,0)):
			gt.set( rowCur, colCur, grid.GetColLabelValue(col), GrowTable.bold )
			colCur += 1
	rowCur += 1
	gt.hLine( rowCur-1, 1, gt.getNumberCols(), False )
	gt.hLine( rowCur, 1, gt.getNumberCols(), True )
	
	# Find the maximum number of places for points.
	for rowMax in xrange(gridPoints.GetNumberRows()):
		if gridPoints.GetCellValue(rowMax, 2) == u'0':
			break
	
	# Add the values from the points and sprint tables.
	for row in xrange(rowMax):
		colCur = 0
		for grid in [gridPoints, gridSprint]:
			for col in xrange(maxSprints if grid == gridSprint else grid.GetNumberCols() - colAdjust.get(grid,0)):
				gt.set( rowCur, colCur, grid.GetCellValue(row,col) )
				colCur += 1
		rowCur += 1
		gt.hLine( rowCur, 1, colCur )
		
	for col in xrange( 1, colCur+1 ):
		gt.vLine( col, 0, rowCur )
	upperColMax = colCur
	
	# Collect the worksheet and results information
	gridBib = scoreSheet.worksheet.gridBib
	gridWorksheet = scoreSheet.worksheet.gridWorksheet
	gridResults = scoreSheet.results.gridResults
	
	colAdjust[gridBib] = 1
	
	rowWorksheet = rowCur
	
	titleAttr = GrowTable.bold | GrowTable.alignCentre
	colCur = 0
	for grid in [gridBib, gridWorksheet, gridResults]:
		for col in xrange(maxSprints if grid == gridWorksheet else grid.GetNumberCols() - colAdjust.get(grid,0)):
			gt.set( rowCur, colCur, makeTwoLines(grid.GetColLabelValue(col)), titleAttr )
			colCur += 1
	rowCur += 1
	
	gt.hLine( rowCur-1, 0, colCur, True )
	gt.hLine( rowCur, 0, colCur, True )
	
	# Add the values from the bib, worksheet and results tables.
	for row in xrange(gridWorksheet.GetNumberRows()):
		colCur = 0
		for grid in [gridBib, gridWorksheet, gridResults]:
			if rowMax <= grid.GetNumberRows():
				for col in xrange(maxSprints if grid == gridWorksheet else grid.GetNumberCols() - colAdjust.get(grid,0)):
					gt.set( rowCur, colCur, grid.GetCellValue(row,col) )
					colCur += 1
		rowCur += 1
		gt.hLine( rowCur, 0, colCur )
		
	for col in xrange( 0, gt.getNumberCols()+1 ):
		gt.vLine( col, rowWorksheet, rowCur )
	
	gt.vLine( 3, 0, gt.getNumberRows(), True )
	gt.vLine( upperColMax, 0, gt.getNumberRows(), True )
	
	# Format the notes assuming a minimum readable size.
	notesHeight = 0
	gtNotes = None
	
	lines = [line for line in race.notes.split(u'\n') if line.strip()]
	if lines:
		gtNotes = GrowTable()
		maxLinesPerCol = 10
		numCols = int(math.ceil(len(lines) / float(maxLinesPerCol)))
		numRows = int(math.ceil(len(lines) / float(numCols)))
		rowCur, colCur = 0, 0
		for i, line in enumerate(lines):
			gtNotes.set( rowCur, colCur*2, u'{}.'.format(i+1), GrowTable.alignRight )
			gtNotes.set( rowCur, colCur*2+1, u'{}    '.format(line.strip()), GrowTable.alignLeft )
			rowCur += 1
			if rowCur == numRows:
				rowCur = 0
				colCur += 1
		lineHeight = heightPix // 65
		notesHeight = (lineHeight+1) * numRows
	
	gt.drawToFitDC( dc, xLeft, yTop, widthFieldPix, heightPix - borderPix - yTop - notesHeight )
	
	# Use any remaining space on the page for the notes.
	if gtNotes:
		notesTop = yTop + gt.height + lineHeight
		gtNotes.drawToFitDC( dc, xLeft, notesTop, widthFieldPix, heightPix - borderPix - notesTop )
	
	# Add a timestamp footer.
	fontSize = heightPix//85
	font = wx.FontFromPixelSize( wx.Size(0,fontSize), wx.FONTFAMILY_SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL )
	dc.SetFont( font )
	text = u'Generated {}'.format( datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S') )
	footerTop = heightPix - borderPix + fontSize/2
	dc.DrawText( text, widthPix - borderPix - dc.GetTextExtent(text)[0], footerTop )
	
	# Add branding
	text = u'Powered by PointsRaceMgr'
	dc.DrawText( text, borderPix, footerTop )

