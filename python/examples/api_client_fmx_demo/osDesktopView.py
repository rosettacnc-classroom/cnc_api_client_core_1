import os
from delphifmx import *

class DesktopView(Form):

    def __init__(self, owner):
        self.MCSTitleLabel = None
        self.MCSXLabel = None
        self.MCSXValue = None
        self.MCSYLabel = None
        self.MCSYValue = None
        self.MCSZLabel = None
        self.MCSZValue = None
        self.MCSALabel = None
        self.MCSAValue = None
        self.MCSBLabel = None
        self.MCSBValue = None
        self.MCSCLabel = None
        self.MCSCValue = None
        self.PRPTitleLabel = None
        self.WCSXLabel = None
        self.WCSXValue = None
        self.WCSYLabel = None
        self.WCSYValue = None
        self.WCSZLabel = None
        self.WCSZValue = None
        self.WCSALabel = None
        self.WCSAValue = None
        self.WCSBLabel = None
        self.WCSBValue = None
        self.WCSCLabel = None
        self.WCSCValue = None
        self.AVLTitleLabel = None
        self.AVLXLabel = None
        self.AVLXValue = None
        self.AVLYLabel = None
        self.AVLYValue = None
        self.AVLZLabel = None
        self.AVLZValue = None
        self.AVLALabel = None
        self.AVLAValue = None
        self.AVLBLabel = None
        self.AVLBValue = None
        self.AVLCLabel = None
        self.AVLCValue = None
        self.WOFTitleLabel = None
        self.WOFXLabel = None
        self.WOFXValue = None
        self.WOFYLabel = None
        self.WOFYValue = None
        self.WOFZLabel = None
        self.WOFZValue = None
        self.WOFALabel = None
        self.WOFAValue = None
        self.WOFBLabel = None
        self.WOFBValue = None
        self.WOFCLabel = None
        self.WOFCValue = None
        self.MTPTitleLabel = None
        self.MTPXLabel = None
        self.MTPXValue = None
        self.MTPYLabel = None
        self.MTPYValue = None
        self.MTPZLabel = None
        self.MTPZValue = None
        self.MTPALabel = None
        self.MTPAValue = None
        self.MTPBLabel = None
        self.MTPBValue = None
        self.MTPCLabel = None
        self.MTPCValue = None
        self.PTPTitleLabel = None
        self.PTPXLabel = None
        self.PTPXValue = None
        self.PTPYLabel = None
        self.PTPYValue = None
        self.PTPZLabel = None
        self.PTPZValue = None
        self.PTPALabel = None
        self.PTPAValue = None
        self.PTPBLabel = None
        self.PTPBValue = None
        self.PTPCLabel = None
        self.PTPCValue = None
        self.TabControl = None
        self.TabProgram = None
        self.NewProgramLabel = None
        self.NewProgramLine = None
        self.ProgramNewButton = None
        self.LoadProgramLabel = None
        self.LoadProgramLine = None
        self.ProgramLoadButton = None
        self.ProgramLoadFileNameEdit = None
        self.SaveProgramLabel = None
        self.SaveProgramLine = None
        self.ProgramSaveFileNameEdit = None
        self.ProgramSaveButton = None
        self.SelectFileButton = None
        self.Button1 = None
        self.Line1 = None
        self.Label1 = None
        self.TabGCode = None
        self.ProgramGCodeSetTextMemo = None
        self.ProgramGCodeSetTextButton = None
        self.ProgramGCodeAddTextButton = None
        self.ProgramGCodeClearButton = None
        self.ProgramGCodeAddTextEdit = None
        self.TabCNC = None
        self.CNCStartButton = None
        self.CNCPauseButton = None
        self.CNCStopButton = None
        self.CNCContinueButton = None
        self.CNCStartFromLineButton = None
        self.CNCResumeAfterStopButton = None
        self.CNCResumeAfterStopFromLineButton = None
        self.CNCCommandsLine = None
        self.CNCCommandsLabel = None
        self.CNCCommandsSpecialLabel = None
        self.CNCCommandsSpecialLine = None
        self.CNCStartFromLineEdit = None
        self.CNCResumeAfterStopFromLineEdit = None
        self.ProgramAnalysisMTButton = None
        self.ProgramAnalysisRTButton = None
        self.ProgramAnalysisRFButton = None
        self.ProgramAnalysisRVButton = None
        self.ProgramAnalysisRZButton = None
        self.ProgramAnalysisLabel = None
        self.ProgramAnalysisLine = None
        self.ProgramAnalysisAbortButton = None
        self.CompilationStateLabel = None
        self.CompilationMessageLabel = None
        self.TabJOG = None
        self.CNCJogCommandXMButton = None
        self.CNCJogCommandXPButton = None
        self.CNCJogCommandYMButton = None
        self.CNCJogCommandYPButton = None
        self.CNCJogCommandZMButton = None
        self.CNCJogCommandZPButton = None
        self.CNCJogCommandAMButton = None
        self.CNCJogCommandAPButton = None
        self.CNCJogCommandBMButton = None
        self.CNCJogCommandBPButton = None
        self.CNCJogCommandCMButton = None
        self.CNCJogCommandCPButton = None
        self.JOGSTOPButton = None
        self.SetProgramPositionXButton = None
        self.SetProgramPositionYButton = None
        self.SetProgramPositionZButton = None
        self.SetProgramPositionAButton = None
        self.SetProgramPositionBButton = None
        self.SetProgramPositionCButton = None
        self.SetProgramPositionXEdit = None
        self.SetProgramPositionYEdit = None
        self.SetProgramPositionZEdit = None
        self.SetProgramPositionAEdit = None
        self.SetProgramPositionBEdit = None
        self.SetProgramPositionCEdit = None
        self.JOGSetSeparatorLine = None
        self.TextAxisPositionText = None
        self.TabOverrides = None
        self.OverrideJog = None
        self.OverrideSpindle = None
        self.OverrideFast = None
        self.OverrideFeed = None
        self.OverrideFeedCustom1 = None
        self.OverrideFeedCustom2 = None
        self.OverrideJogLabel = None
        self.OverrideSpindleLabel = None
        self.OverrideFastLabel = None
        self.OverrideFeedLabel = None
        self.OverrideFeedCustom1Label = None
        self.OverrideFeedCustom2Label = None
        self.OverrideJogValue = None
        self.OverrideSpindleValue = None
        self.OverrideFastValue = None
        self.OverrideFeedValue = None
        self.OverrideFeedCustom1Value = None
        self.OverrideFeedCustom2Value = None
        self.TabHoming = None
        self.HomingXButton = None
        self.HomingYButton = None
        self.HomingZButton = None
        self.HomingAButton = None
        self.HomingCButton = None
        self.HomingAllButton = None
        self.HomingBButton = None
        self.HomingSTOPButton = None
        self.HomingXState = None
        self.HomingYState = None
        self.HomingZState = None
        self.HomingAState = None
        self.HomingBState = None
        self.HomingCState = None
        self.HomingAllState = None
        self.TabMDI = None
        self.CNCMDICommandMemo = None
        self.CNCMDICommandButton = None
        self.TabDIO = None
        self.DIOImage = None
        self.DigitalInputsRadioButton = None
        self.DigitalOutputsRadioButton = None
        self.TabAIO = None
        self.ANITitleLabel = None
        self.ANI01Label = None
        self.ANI02Label = None
        self.ANI03Label = None
        self.ANI04Label = None
        self.ANI05Label = None
        self.ANI06Label = None
        self.ANI07Label = None
        self.ANI08Label = None
        self.ANI01Value = None
        self.ANI02Value = None
        self.ANI03Value = None
        self.ANI04Value = None
        self.ANI05Value = None
        self.ANI06Value = None
        self.ANI07Value = None
        self.ANI08Value = None
        self.ANI09Label = None
        self.ANI09Value = None
        self.ANI10Value = None
        self.ANI10Label = None
        self.ANI11Label = None
        self.ANI11Value = None
        self.ANI12Value = None
        self.ANI12Label = None
        self.ANI13Label = None
        self.ANI13Value = None
        self.ANI14Value = None
        self.ANI14Label = None
        self.ANI15Label = None
        self.ANI15Value = None
        self.ANI16Value = None
        self.ANI16Label = None
        self.ANO16Value = None
        self.ANO16Label = None
        self.ANO15Label = None
        self.ANO15Value = None
        self.ANO14Value = None
        self.ANO14Label = None
        self.ANO13Label = None
        self.ANO13Value = None
        self.ANO12Value = None
        self.ANO12Label = None
        self.ANO11Label = None
        self.ANO11Value = None
        self.ANO10Value = None
        self.ANO10Label = None
        self.ANO09Label = None
        self.ANO09Value = None
        self.ANO01Value = None
        self.ANO01Label = None
        self.ANO02Label = None
        self.ANO02Value = None
        self.ANO03Value = None
        self.ANO03Label = None
        self.ANO04Label = None
        self.ANO04Value = None
        self.ANO05Value = None
        self.ANO05Label = None
        self.ANO06Label = None
        self.ANO06Value = None
        self.ANO07Value = None
        self.ANO07Label = None
        self.ANO08Label = None
        self.ANO08Value = None
        self.ANOTitleLabel = None
        self.TabScanningLaser = None
        self.LaserZeroXAxisButton = None
        self.LaserOutBitLabel = None
        self.LaserOutBitValue = None
        self.LaserOutUMFLabel = None
        self.LaserHMeasureLabel = None
        self.LaserOutUMFValue = None
        self.LaserHMeasureValue = None
        self.LaserMCSXPositionLabel = None
        self.LaserMCSXPositionValue = None
        self.LaserInfoLabel = None
        self.LaserMCSYPositionLabel = None
        self.LaserMCSYPositionValue = None
        self.LaserMCSZPositionLabel = None
        self.LaserMCSZPositionValue = None
        self.LaserZeroYAxisButton = None
        self.LaserZeroZAxisButton = None
        self.TabMachiningInfo = None
        self.MachiningInfoImage = None
        self.TCPExtentsInfoRadioButton = None
        self.JointsInfoRadioButton = None
        self.UsedToolInfoRadioButton = None
        self.TabSystemInfo = None
        self.SystemInfoMemo = None
        self.JOPTitleLabel = None
        self.JOPXLabel = None
        self.JOPXValue = None
        self.JOPYLabel = None
        self.JOPYValue = None
        self.JOPZLabel = None
        self.JOPZValue = None
        self.JOPALabel = None
        self.JOPAValue = None
        self.JOPBLabel = None
        self.JOPBValue = None
        self.JOPCLabel = None
        self.JOPCValue = None
        self.UpdateTimer = None
        self.StatusBar = None
        self.StateMachineLabel = None
        self.APIServerConnectionStateLabel = None
        self.APIServerHostPortLabel = None
        self.APIServerHostEdit = None
        self.APIServerPortEdit = None
        self.ServerConnectDisconnectButton = None
        self.StayOnTopCheckBox = None
        self.MachineInfoLabel = None
        self.WorkedTimeLabel = None
        self.WorkedTimeValue = None
        self.GCodeLineLabel = None
        self.GCodeLineValue = None
        self.SpindleStatusLabel = None
        self.SpindleStatusValue = None
        self.CoolantMistLabel = None
        self.CoolantMistValue = None
        self.CoolantFloodLabel = None
        self.CoolantFloodValue = None
        self.ToolInfoPanel = None
        self.ToolInfoLabel = None
        self.UseTLSCheckBox = None
        self.PlannedTimeLabel = None
        self.PlannedTimeValue = None
        self.Panel1 = None
        self.ResetAlarmsButton = None
        self.ResetAlarmsHistoryButton = None
        self.ResetWarningsButton = None
        self.ResetWarningsHistoryButton = None
        self.CommandsLabel = None
        self.TBCNCStartButton = None
        self.TBCNCStopButton = None
        self.TBCNCPauseButton = None
        self.TBCNCContinueButton = None
        self.TBCNCResumeAfterStopButton = None
        self.OpenDialog = None
        self.ActionList = None
        self.CNCContinueAction = None
        self.CNCHomingAAction = None
        self.CNCHomingAllAction = None
        self.CNCHomingBAction = None
        self.CNCHomingCAction = None
        self.CNCHomingXAction = None
        self.CNCHomingYAction = None
        self.CNCHomingZAction = None
        self.CNCMDICommandAction = None
        self.CNCPauseAction = None
        self.CNCResumeAfterStopAction = None
        self.CNCResumeAfterStopFromLineAction = None
        self.CNCStartAction = None
        self.CNCStartFromLineAction = None
        self.CNCStopAction = None
        self.LaserZeroXAxisAction = None
        self.LaserZeroYAxisAction = None
        self.LaserZeroZAxisAction = None
        self.ProgramAnalysisAbortAction = None
        self.ProgramAnalysisMTAction = None
        self.ProgramAnalysisRFAction = None
        self.ProgramAnalysisRTAction = None
        self.ProgramAnalysisRVAction = None
        self.ProgramAnalysisRZAction = None
        self.ProgramGCodeAddTextAction = None
        self.ProgramGCodeClearAction = None
        self.ProgramGCodeSetTextAction = None
        self.ResetAlarmsAction = None
        self.ResetAlarmsHistoryAction = None
        self.ResetWarningsAction = None
        self.ResetWarningsHistoryAction = None
        self.ProgramLoadAction = None
        self.ProgramNewAction = None
        self.ProgramSaveAction = None
        self.ProgramSaveAsAction = None
        self.ServerConnectDisconnectAction = None
        self.SetProgramPositionXAction = None
        self.SetProgramPositionYAction = None
        self.SetProgramPositionZAction = None
        self.SetProgramPositionAAction = None
        self.SetProgramPositionBAction = None
        self.SetProgramPositionCAction = None
        self.SelectFileAction = None
        self.LoadProps(os.path.join(os.path.dirname(os.path.abspath(__file__)), "osDesktopView.pyfmx"))

    def FormCreate(self, Sender):
        pass

    def FormDestroy(self, Sender):
        pass

    def TabControlChange(self, Sender):
        pass

    def ActionMainExecute(self, Sender):
        pass

    def EditKeyDown(self, Sender, Key, KeyChar, Shift):
        pass

    def EditExit(self, Sender):
        pass

    def CNCJogCommandMouseDown(self, Sender, Button, Shift, X, Y):
        pass

    def CNCJogCommandMouseUp(self, Sender, Button, Shift, X, Y):
        pass

    def EditClick(self, Sender):
        pass

    def EditEnter(self, Sender):
        pass

    def OverrideChange(self, Sender):
        pass

    def UpdateTimerTimer(self, Sender):
        pass

    def CheckBoxChange(self, Sender):
        pass

    def ActionMainUpdate(self, Sender):
        pass