import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from Editor import EditorWidget

#
# VolumeClipIntegration
#

class VolumeClipIntegration(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "VolumeClipIntegration" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["Peter Behringer"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    """
    self.parent.acknowledgementText = """ self.parent.acknowledgementText """


#
# VolumeClipIntegrationWidget
#

class VolumeClipIntegrationWidget(ScriptedLoadableModuleWidget):

  def __init__(self, parent):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.logic = VolumeClipIntegrationLogic()


  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
    self.inputSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 0 )
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("T2 Volume: ", self.inputSelector)


    #
    # Start Prostate Segmentation Button
    #
    self.applyButton = qt.QPushButton("Start Prostate Segmentation")
    self.applyButton.enabled = True
    parametersFormLayout.addRow(self.applyButton)

    #
    # Apply Segmentation
    #

    self.applyButton2 = qt.QPushButton("Apply Segmentation")
    self.applyButton2.toolTip = "Run the algorithm."
    self.applyButton2.enabled = True
    parametersFormLayout.addRow(self.applyButton2)


    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.applyButton2.connect('clicked(bool)', self.onApplyButton2)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode()

  def onApplyButton(self):
    logic = VolumeClipIntegrationLogic()

    print("onApplyButton")
    logic.run(self.inputSelector.currentNode())

  def onApplyButton2(self):
    logic = VolumeClipIntegrationLogic()
    print("onApplyButton2")

    # initialize Label Map
    outputLabelMap=slicer.vtkMRMLScalarVolumeNode()
    outputLabelMap.SetLabelMap(1)
    slicer.mrmlScene.AddNode(outputLabelMap)

    # get clippingModel Node
    clipModelNode=slicer.mrmlScene.GetNodesByName('clipModelNode')
    clippingModel=clipModelNode.GetItemAsObject(0)

    # run CLI-Module
    logic.modelToLabelmap(self.inputSelector.currentNode(),clippingModel,outputLabelMap)

    # set Label Outline
    slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeRed").SetUseLabelOutline(True)
    slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeYellow").SetUseLabelOutline(True)
    slicer.mrmlScene.GetNodeByID("vtkMRMLSliceNodeGreen").SetUseLabelOutline(True)


#
# VolumeClipIntegrationLogic
#

class VolumeClipIntegrationLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is a dummy logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      print('no volume node')
      return False
    if volumeNode.GetImageData() == None:
      print('no image data')
      return False
    return True


  def run(self,inputVolume):
    """
    Run the actual algorithm
    """

    self.delayDisplay('Set Volume Clip User Mode')

    # set four up view, select persistent fiducial marker as crosshair
    self.setVolumeClipUserMode()

    # let user place Fiducials
    self.placeFiducials()

    # timer test
    # self.timer()

    return True

  def setVolumeClipUserMode(self):

    # set Four Up View
    lm=slicer.app.layoutManager()
    lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)

    # set the mouse mode into Markups fiducial placement
    placeModePersistence = 1
    slicer.modules.markups.logic().StartPlaceMode(placeModePersistence)

    return True


  def updateModel(self,observer,caller):

    clipModelNode=slicer.mrmlScene.GetNodesByName('clipModelNode')
    clippingModel=clipModelNode.GetItemAsObject(0)

    inputMarkupNode=slicer.mrmlScene.GetNodesByName('inputMarkupNode')
    inputMarkup=inputMarkupNode.GetItemAsObject(0)

    import VolumeClipWithModel
    clipLogic=VolumeClipWithModel.VolumeClipWithModelLogic()
    clipLogic.updateModelFromMarkup(inputMarkup, clippingModel)

  def placeFiducials(self):

    # Create empty model node
    clippingModel = slicer.vtkMRMLModelNode()
    clippingModel.SetName('clipModelNode')
    slicer.mrmlScene.AddNode(clippingModel)

    # Create markup display fiducials - why do i need that?
    displayNode = slicer.vtkMRMLMarkupsDisplayNode()
    slicer.mrmlScene.AddNode(displayNode)

    # create markup fiducial node
    inputMarkup = slicer.vtkMRMLMarkupsFiducialNode()
    inputMarkup.SetName('inputMarkupNode')
    slicer.mrmlScene.AddNode(inputMarkup)
    inputMarkup.SetAndObserveDisplayNodeID(displayNode.GetID())

    # add Observer
    inputMarkup.AddObserver(vtk.vtkCommand.ModifiedEvent,self.updateModel)

    return True

  def modelToLabelmap(self,inputVolume,inputModel,outputLabelMap):

    """
    PARAMETER FOR MODELTOLABELMAP CLI MODULE:
    Parameter (0/0): sampleDistance
    Parameter (0/1): labelValue
    Parameter (1/0): InputVolume
    Parameter (1/1): surface
    Parameter (1/2): OutputVolume
    """

    # define params
    params = {'sampleDistance': 0.1, 'labelValue': 5, 'InputVolume' : inputVolume, 'surface' : inputModel, 'OutputVolume' : outputLabelMap}

    # run ModelToLabelMap-CLI Module
    slicer.cli.run(slicer.modules.modeltolabelmap, None, params)

    return True

  # def timer(self):
  #  s=0
  #  import time
  #  while s<=10:
  #   print ('timer')
  #    time.sleep(1)
  #   s += 1

class VolumeClipIntegrationTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_VolumeClipIntegration1()

  def test_VolumeClipIntegration1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests sould exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        print('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        print('Loading %s...\n' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading\n')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = VolumeClipIntegrationLogic()
    self.assertTrue( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
