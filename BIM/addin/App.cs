using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Electrical;
using Autodesk.Revit.DB.Events;
using Autodesk.Revit.DB.Mechanical;
using Autodesk.Revit.DB.Plumbing;
using Autodesk.Revit.DB.Structure;
using Autodesk.Revit.UI;
using Autodesk.Revit.UI.Events;

namespace PrefabBIM
{
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class App : IExternalApplication
    {
        private static UIControlledApplication? _uiControlledApp;
        private static readonly object _logLock = new object();
        private static string _activeJobMode = "none";

        private static readonly string BimDir = @"C:\Users\rashe\Documents\prefab\repo\BIM";
        private static readonly string LogFilePathStructural = Path.Combine(BimDir, "build_log.txt");
        private static readonly string LogFilePathMep = Path.Combine(BimDir, "build_log_mep.txt");
        private static readonly string LogFilePathSub = Path.Combine(BimDir, "build_log_sub.txt");
        private static string _currentLogPath = LogFilePathStructural;

        // Structural Model Paths
        private static readonly string RepoRootDir = @"C:\Users\rashe\Documents\prefab\repo";
        private static readonly string PileDesignJsonPath = Path.Combine(RepoRootDir, "Paper2_Structural", "analysis", "2_Precast", "reactions_M2_fix600", "pile_design_Qa1307.json");
        private static readonly string StructuralTemplatePath = @"C:\ProgramData\Autodesk\RVT 2027\Templates\English\Structural Analysis-DefaultMetric.rte";
        private static readonly string RvtPath = Path.Combine(BimDir, "Prefab_RCC_10storey.rvt");
        private static readonly string IfcFileName = "Prefab_RCC_10storey.ifc";
        private static readonly string PngPath = Path.Combine(BimDir, "Prefab_RCC_10storey_3D.png");
        private static readonly string FoundationsPngPath = Path.Combine(BimDir, "Prefab_RCC_10storey_foundations_3D.png");

        // MEP Model Paths
        private static readonly string MepTemplatePath = @"C:\ProgramData\Autodesk\RVT 2027\Templates\English\Systems-Default_Metric.rte";
        private static readonly string MepRvtPath = Path.Combine(BimDir, "Prefab_RCC_10storey_MEP.rvt");
        private static readonly string MepIfcFileName = "Prefab_RCC_10storey_MEP.ifc";
        private static readonly string MepPngPath = Path.Combine(BimDir, "Prefab_RCC_10storey_MEP_3D.png");

        public Result OnStartup(UIControlledApplication application)
        {
            _uiControlledApp = application;

            var jobEnv = Environment.GetEnvironmentVariable("PREFAB_BIM_JOB");
            if (string.Equals(jobEnv, "1", StringComparison.OrdinalIgnoreCase))
            {
                _activeJobMode = "structural";
                _currentLogPath = LogFilePathStructural;
            }
            else if (string.Equals(jobEnv, "mep", StringComparison.OrdinalIgnoreCase))
            {
                _activeJobMode = "mep";
                _currentLogPath = LogFilePathMep;
            }
            else if (string.Equals(jobEnv, "sub", StringComparison.OrdinalIgnoreCase))
            {
                _activeJobMode = "sub";
                _currentLogPath = LogFilePathSub;
            }
            else
            {
                // Standby mode: do nothing
                return Result.Succeeded;
            }

            Log("================================================================================");
            Log($"PrefabBIM Add-in started. PREFAB_BIM_JOB='{jobEnv}' detected. Active mode: '{_activeJobMode}'.");
            Log("================================================================================");

            try
            {
                // Subscribe to ApplicationInitialized to start model generation
                application.ControlledApplication.ApplicationInitialized += OnApplicationInitialized;

                // Subscribe to DialogBoxShowing to suppress any interactive UI dialogs
                application.DialogBoxShowing += OnDialogBoxShowing;

                Log("Subscribed to ApplicationInitialized and DialogBoxShowing successfully.");
            }
            catch (Exception ex)
            {
                Log($"FATAL: Failed to subscribe to application startup events: {ex}");
                return Result.Failed;
            }

            return Result.Succeeded;
        }

        public Result OnShutdown(UIControlledApplication application)
        {
            Log($"PrefabBIM Add-in shutting down (Mode: {_activeJobMode}).");
            return Result.Succeeded;
        }

        private static void OnDialogBoxShowing(object? sender, DialogBoxShowingEventArgs e)
        {
            try
            {
                Log($"[DIALOG SUPPRESSION] DialogBoxShowing: DialogId = '{e.DialogId}'");
                if (e is TaskDialogShowingEventArgs tdArgs)
                {
                    Log($"[DIALOG SUPPRESSION] TaskDialog: Id = '{tdArgs.DialogId}', Message = '{tdArgs.Message}'");
                    tdArgs.OverrideResult((int)TaskDialogResult.Ok);
                }
                else
                {
                    e.OverrideResult(1); // Standard Win32 IDOK
                }
            }
            catch (Exception ex)
            {
                Log($"[DIALOG SUPPRESSION ERROR] {ex.Message}");
            }
        }

        private static void OnFailuresProcessing(object? sender, FailuresProcessingEventArgs e)
        {
            try
            {
                var accessor = e.GetFailuresAccessor();
                var failures = accessor.GetFailureMessages();
                foreach (var fail in failures)
                {
                    var severity = fail.GetSeverity();
                    if (severity == FailureSeverity.Warning)
                    {
                        accessor.DeleteWarning(fail);
                    }
                    else if (severity == FailureSeverity.Error)
                    {
                        if (fail.HasResolutions() && accessor.CanCommitPendingTransaction())
                        {
                            accessor.ResolveFailure(fail);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Log($"[FAILURES PROCESSING ERROR] {ex.Message}");
            }
        }

        private static void OnApplicationInitialized(object? sender, ApplicationInitializedEventArgs e)
        {
            Log($"ApplicationInitialized event fired. Executing pipeline for mode: '{_activeJobMode}'...");

            if (sender is not Autodesk.Revit.ApplicationServices.Application app)
            {
                Log("ERROR: Sender is not Autodesk.Revit.ApplicationServices.Application. Aborting.");
                return;
            }

            // Hook FailuresProcessing on Revit application to suppress warnings
            app.FailuresProcessing += OnFailuresProcessing;

            bool buildSuccess = false;
            try
            {
                if (_activeJobMode == "structural")
                {
                    buildSuccess = ExecuteBimGeneration(app);
                }
                else if (_activeJobMode == "mep")
                {
                    buildSuccess = ExecuteMepPipeline(app);
                }
                else if (_activeJobMode == "sub")
                {
                    buildSuccess = ExecuteSubPipeline(app);
                }
            }
            catch (Exception ex)
            {
                Log($"FATAL UNHANDLED EXCEPTION in {_activeJobMode} execution: {ex}");
            }

            Log($"Job execution finished with result: {(buildSuccess ? "SUCCESS" : "FAILED")}. Registering Idling event for Revit exit...");

            // Subscribe to Idling to post the ExitRevit command safely
            if (_uiControlledApp != null)
            {
                _uiControlledApp.Idling += OnIdlingExit;
            }
        }

        private static void OnIdlingExit(object? sender, IdlingEventArgs e)
        {
            try
            {
                if (_uiControlledApp != null)
                {
                    _uiControlledApp.Idling -= OnIdlingExit;
                }

                if (sender is UIApplication uiApp)
                {
                    uiApp.Idling -= OnIdlingExit;

                    Log("Idling triggered after document closed. Posting ExitRevit command...");
                    var exitCommandId = RevitCommandId.LookupPostableCommandId(PostableCommand.ExitRevit);
                    if (exitCommandId != null && uiApp.CanPostCommand(exitCommandId))
                    {
                        uiApp.PostCommand(exitCommandId);
                        Log("ExitRevit command posted successfully.");
                    }
                    else
                    {
                        Log("WARNING: Cannot post ExitRevit command directly.");
                    }
                }
            }
            catch (Exception ex)
            {
                Log($"Exception in OnIdlingExit: {ex}");
            }
        }

        // =========================================================================
        // JOB 1: Structural Model Generation (PREFAB_BIM_JOB=1)
        // =========================================================================
        private static bool ExecuteBimGeneration(Autodesk.Revit.ApplicationServices.Application app)
        {
            if (!File.Exists(StructuralTemplatePath))
            {
                Log($"ERROR: Template file does not exist at '{StructuralTemplatePath}'");
                return false;
            }

            if (!Directory.Exists(BimDir))
            {
                Directory.CreateDirectory(BimDir);
            }

            Log($"Opening template project: {StructuralTemplatePath}");
            Document doc = app.NewProjectDocument(StructuralTemplatePath);
            if (doc == null)
            {
                Log("ERROR: Failed to create new project document from template.");
                return false;
            }

            int columnsCreated = 0;
            int beamsCreated = 0;
            int wallsCreated = 0;
            int floorsCreated = 0;
            int failureCount = 0;

            try
            {
                // -------------------------------------------------------------
                // Phase 1: Levels, Grids, and Material
                // -------------------------------------------------------------
                var levels = new Level[11]; // levels[0] = Base, levels[1..10] = Level 1..10
                Material? concreteMaterial = null;

                using (var tx = new Transaction(doc, "Setup Levels, Grids and Material"))
                {
                    tx.Start();

                    // Material creation: "Concrete C28 (precast)"
                    concreteMaterial = new FilteredElementCollector(doc)
                        .OfClass(typeof(Material))
                        .Cast<Material>()
                        .FirstOrDefault(m => m.Name.Equals("Concrete C28 (precast)", StringComparison.OrdinalIgnoreCase));

                    if (concreteMaterial == null)
                    {
                        var matId = Material.Create(doc, "Concrete C28 (precast)");
                        concreteMaterial = doc.GetElement(matId) as Material;
                        if (concreteMaterial != null)
                        {
                            concreteMaterial.MaterialClass = "Concrete";
                            concreteMaterial.Color = new Color(200, 200, 200); // Light grey
                            concreteMaterial.Transparency = 0;
                            Log($"Created material: '{concreteMaterial.Name}' (Class: Concrete, Shading: RGB 200,200,200)");
                        }
                    }
                    else
                    {
                        Log($"Reusing existing material: '{concreteMaterial.Name}'");
                    }

                    // Levels setup: Base at 0m, Level 1..10 at 3, 6, ..., 30m
                    var existingLevels = new FilteredElementCollector(doc)
                        .OfClass(typeof(Level))
                        .Cast<Level>()
                        .ToList();

                    // Temporarily rename existing levels to prevent naming collisions
                    for (int i = 0; i < existingLevels.Count; i++)
                    {
                        existingLevels[i].Name = $"_tmp_lvl_{Guid.NewGuid():N}";
                    }

                    for (int i = 0; i <= 10; i++)
                    {
                        string lvlName = (i == 0) ? "Base" : $"Level {i}";
                        double elevM = i * 3.0;
                        double elevFt = MToFt(elevM);

                        Level lvl;
                        if (i < existingLevels.Count)
                        {
                            lvl = existingLevels[i];
                            lvl.Elevation = elevFt;
                            lvl.Name = lvlName;
                        }
                        else
                        {
                            lvl = Level.Create(doc, elevFt);
                            lvl.Name = lvlName;
                        }
                        levels[i] = lvl;
                        Log($"Level [{i}]: '{lvl.Name}', Elevation = {elevM:F1} m ({elevFt:F3} ft)");
                    }

                    // Delete extra levels if template had more than 11
                    for (int i = 11; i < existingLevels.Count; i++)
                    {
                        try { doc.Delete(existingLevels[i].Id); } catch { }
                    }

                    // Grids setup: A-E at x = 0, 5, 10, 15, 20m; 1-4 at y = 0, 5, 10, 15m
                    var existingGrids = new FilteredElementCollector(doc).OfClass(typeof(Grid)).ToList();
                    foreach (var g in existingGrids)
                    {
                        try { doc.Delete(g.Id); } catch { }
                    }

                    double[] xCoords = { 0.0, 5.0, 10.0, 15.0, 20.0 };
                    string[] xNames = { "A", "B", "C", "D", "E" };
                    for (int xi = 0; xi < xCoords.Length; xi++)
                    {
                        var start = new XYZ(MToFt(xCoords[xi]), MToFt(-2.0), 0);
                        var end = new XYZ(MToFt(xCoords[xi]), MToFt(17.0), 0);
                        var grid = Grid.Create(doc, Line.CreateBound(start, end));
                        grid.Name = xNames[xi];
                        Log($"Grid created: '{grid.Name}' at x = {xCoords[xi]} m");
                    }

                    double[] yCoords = { 0.0, 5.0, 10.0, 15.0 };
                    string[] yNames = { "1", "2", "3", "4" };
                    for (int yi = 0; yi < yCoords.Length; yi++)
                    {
                        var start = new XYZ(MToFt(-2.0), MToFt(yCoords[yi]), 0);
                        var end = new XYZ(MToFt(22.0), MToFt(yCoords[yi]), 0);
                        var grid = Grid.Create(doc, Line.CreateBound(start, end));
                        grid.Name = yNames[yi];
                        Log($"Grid created: '{grid.Name}' at y = {yCoords[yi]} m");
                    }

                    tx.Commit();
                }

                // -------------------------------------------------------------
                // Phase 2: Families & Types (Columns, Beams, Walls, Floors)
                // -------------------------------------------------------------
                FamilySymbol? symCol500 = null;
                FamilySymbol? symCol600 = null;
                FamilySymbol? symBeam300x500 = null;
                WallType? pcWallType = null;
                FloorType? pcFloorType = null;

                using (var tx = new Transaction(doc, "Create Element Types"))
                {
                    tx.Start();

                    var matId = concreteMaterial?.Id ?? ElementId.InvalidElementId;

                    // 1. Column Family Symbols: OST_StructuralColumns
                    var colSymbols = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_StructuralColumns)
                        .OfClass(typeof(FamilySymbol))
                        .Cast<FamilySymbol>()
                        .ToList();

                    Log($"Found {colSymbols.Count} structural column symbols in template.");
                    foreach (var s in colSymbols)
                    {
                        Log($"  Column Family: '{s.FamilyName}', Symbol: '{s.Name}'");
                    }

                    var baseColSymbol = colSymbols.FirstOrDefault(s =>
                        (s.FamilyName.Contains("Concrete", StringComparison.OrdinalIgnoreCase) || s.Name.Contains("Concrete", StringComparison.OrdinalIgnoreCase)) &&
                        (s.FamilyName.Contains("Rect", StringComparison.OrdinalIgnoreCase) || s.Name.Contains("Rect", StringComparison.OrdinalIgnoreCase)));

                    if (baseColSymbol == null)
                    {
                        baseColSymbol = colSymbols.FirstOrDefault(s => s.FamilyName.Contains("Rect", StringComparison.OrdinalIgnoreCase) || s.Name.Contains("Rect", StringComparison.OrdinalIgnoreCase))
                                     ?? colSymbols.FirstOrDefault();
                        Log($"WARNING: Concrete rectangular column not found by name. Falling back to: '{baseColSymbol?.FamilyName}' : '{baseColSymbol?.Name}'");
                    }
                    else
                    {
                        Log($"Selected concrete rectangular column base symbol: '{baseColSymbol.FamilyName}' : '{baseColSymbol.Name}'");
                    }

                    if (baseColSymbol == null)
                    {
                        throw new InvalidOperationException("No structural column family found in template.");
                    }

                    symCol500 = GetOrCreateFamilySymbol(baseColSymbol, "C 500x500");
                    SetDimensionParameters(symCol500, MToFt(0.5), MToFt(0.5), matId, "C 500x500");

                    symCol600 = GetOrCreateFamilySymbol(baseColSymbol, "C 600x600");
                    SetDimensionParameters(symCol600, MToFt(0.6), MToFt(0.6), matId, "C 600x600");

                    // 2. Framing Family Symbols: OST_StructuralFraming
                    var beamSymbols = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_StructuralFraming)
                        .OfClass(typeof(FamilySymbol))
                        .Cast<FamilySymbol>()
                        .ToList();

                    Log($"Found {beamSymbols.Count} structural framing symbols in template.");
                    foreach (var s in beamSymbols)
                    {
                        Log($"  Framing Family: '{s.FamilyName}', Symbol: '{s.Name}'");
                    }

                    var baseBeamSymbol = beamSymbols.FirstOrDefault(s =>
                        (s.FamilyName.Contains("Concrete", StringComparison.OrdinalIgnoreCase) || s.Name.Contains("Concrete", StringComparison.OrdinalIgnoreCase)) &&
                        (s.FamilyName.Contains("Rect", StringComparison.OrdinalIgnoreCase) || s.Name.Contains("Rect", StringComparison.OrdinalIgnoreCase)));

                    if (baseBeamSymbol == null)
                    {
                        baseBeamSymbol = beamSymbols.FirstOrDefault(s => s.FamilyName.Contains("Rect", StringComparison.OrdinalIgnoreCase) || s.Name.Contains("Rect", StringComparison.OrdinalIgnoreCase))
                                      ?? beamSymbols.FirstOrDefault();
                        Log($"WARNING: Concrete rectangular framing not found by name. Falling back to: '{baseBeamSymbol?.FamilyName}' : '{baseBeamSymbol?.Name}'");
                    }
                    else
                    {
                        Log($"Selected concrete rectangular framing base symbol: '{baseBeamSymbol.FamilyName}' : '{baseBeamSymbol.Name}'");
                    }

                    if (baseBeamSymbol == null)
                    {
                        throw new InvalidOperationException("No structural framing family found in template.");
                    }

                    symBeam300x500 = GetOrCreateFamilySymbol(baseBeamSymbol, "B 300x500");
                    SetDimensionParameters(symBeam300x500, MToFt(0.3), MToFt(0.5), matId, "B 300x500");

                    // 3. WallType: "PC Wall 200"
                    var baseWallType = new FilteredElementCollector(doc)
                        .OfClass(typeof(WallType))
                        .Cast<WallType>()
                        .FirstOrDefault(wt => wt.Kind == WallKind.Basic);

                    if (baseWallType == null)
                    {
                        throw new InvalidOperationException("No Basic WallType found in template.");
                    }

                    pcWallType = doc.GetElement(baseWallType.Duplicate("PC Wall 200").Id) as WallType;
                    var wallCs = CompoundStructure.CreateSingleLayerCompoundStructure(
                        MaterialFunctionAssignment.Structure,
                        MmToFt(200.0),
                        matId);
                    pcWallType!.SetCompoundStructure(wallCs);
                    Log($"Created WallType: 'PC Wall 200' with single 200 mm concrete layer.");

                    // 4. FloorType: "PC Slab 150"
                    var baseFloorType = new FilteredElementCollector(doc)
                        .OfClass(typeof(FloorType))
                        .Cast<FloorType>()
                        .Where(ft => !ft.IsFoundationSlab && ft.GetCompoundStructure() != null)
                        .FirstOrDefault();

                    if (baseFloorType == null)
                    {
                        throw new InvalidOperationException("No FloorType found in template.");
                    }

                    pcFloorType = doc.GetElement(baseFloorType.Duplicate("PC Slab 150").Id) as FloorType;
                    var floorCs = pcFloorType!.GetCompoundStructure();
                    floorCs.SetLayers(new List<CompoundStructureLayer>
                    {
                        new CompoundStructureLayer(MmToFt(150.0), MaterialFunctionAssignment.Structure, matId)
                    });
                    floorCs.SetNumberOfShellLayers(ShellLayerType.Exterior, 0);
                    floorCs.SetNumberOfShellLayers(ShellLayerType.Interior, 0);
                    floorCs.StructuralMaterialIndex = 0;
                    pcFloorType.SetCompoundStructure(floorCs);
                    Log($"Created FloorType: 'PC Slab 150' with single 150 mm concrete layer.");

                    tx.Commit();
                }

                // -------------------------------------------------------------
                // Phase 3: Model Elements Generation
                // -------------------------------------------------------------
                const string elementComments = "Precast element; Paper 2 scheme M2 + 600x600 boundary columns S1-S3";

                using (var tx = new Transaction(doc, "Generate Structural Elements"))
                {
                    tx.Start();

                    double[] colXs = { 0.0, 5.0, 10.0, 15.0, 20.0 };
                    string[] colXNames = { "A", "B", "C", "D", "E" };
                    double[] colYs = { 0.0, 5.0, 10.0, 15.0 };
                    string[] colYNames = { "1", "2", "3", "4" };

                    // 1. Structural Columns (200 total: 20 per storey × 10 storeys)
                    for (int storey = 1; storey <= 10; storey++)
                    {
                        var baseLvl = levels[storey - 1];
                        var topLvl = levels[storey];

                        for (int xi = 0; xi < colXs.Length; xi++)
                        {
                            for (int yi = 0; yi < colYs.Length; yi++)
                            {
                                double x = colXs[xi];
                                double y = colYs[yi];
                                string gridX = colXNames[xi];
                                string gridY = colYNames[yi];

                                bool isBoundary600 = (storey <= 3) && IsWallEndColumn(x, y);
                                var symbol = isBoundary600 ? symCol600! : symCol500!;

                                try
                                {
                                    var pt = new XYZ(MToFt(x), MToFt(y), baseLvl.Elevation);
                                    var colInstance = doc.Create.NewFamilyInstance(pt, symbol, baseLvl, StructuralType.Column);

                                    var topParam = colInstance.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM);
                                    topParam?.Set(topLvl.Id);

                                    var baseParam = colInstance.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_PARAM);
                                    baseParam?.Set(baseLvl.Id);

                                    var topOffParam = colInstance.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM);
                                    topOffParam?.Set(0.0);

                                    var baseOffParam = colInstance.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM);
                                    baseOffParam?.Set(0.0);

                                    string mark = $"PC-C-{gridX}{gridY}-S{storey}";
                                    SetMarkAndComments(colInstance, mark, elementComments);

                                    columnsCreated++;
                                }
                                catch (Exception ex)
                                {
                                    failureCount++;
                                    Log($"ERROR creating column at ({x},{y}) Storey {storey}: {ex.Message}");
                                }
                            }
                        }
                    }
                    Log($"Columns generated: {columnsCreated} (expected: 200)");

                    // 2. Beams (310 total: 31 per level × 10 levels)
                    for (int storey = 1; storey <= 10; storey++)
                    {
                        var lvl = levels[storey];
                        double z = lvl.Elevation;
                        int beamIndex = 1;

                        // X-direction beams along y = 0, 5, 10, 15 m (4 bays × 4 lines = 16)
                        foreach (double y in colYs)
                        {
                            for (int bay = 0; bay < colXs.Length - 1; bay++)
                            {
                                double x1 = colXs[bay];
                                double x2 = colXs[bay + 1];

                                try
                                {
                                    var p1 = new XYZ(MToFt(x1), MToFt(y), z);
                                    var p2 = new XYZ(MToFt(x2), MToFt(y), z);
                                    var curve = Line.CreateBound(p1, p2);
                                    var beamInstance = doc.Create.NewFamilyInstance(curve, symBeam300x500!, lvl, StructuralType.Beam);

                                    string mark = $"PC-B-L{storey}-{beamIndex++}";
                                    SetMarkAndComments(beamInstance, mark, elementComments);

                                    beamsCreated++;
                                }
                                catch (Exception ex)
                                {
                                    failureCount++;
                                    Log($"ERROR creating X-beam at y={y}, x={x1}->{x2}, Level {storey}: {ex.Message}");
                                }
                            }
                        }

                        // Y-direction beams along x = 0, 5, 10, 15, 20 m (3 bays × 5 lines = 15)
                        foreach (double x in colXs)
                        {
                            for (int bay = 0; bay < colYs.Length - 1; bay++)
                            {
                                double y1 = colYs[bay];
                                double y2 = colYs[bay + 1];

                                try
                                {
                                    var p1 = new XYZ(MToFt(x), MToFt(y1), z);
                                    var p2 = new XYZ(MToFt(x), MToFt(y2), z);
                                    var curve = Line.CreateBound(p1, p2);
                                    var beamInstance = doc.Create.NewFamilyInstance(curve, symBeam300x500!, lvl, StructuralType.Beam);

                                    string mark = $"PC-B-L{storey}-{beamIndex++}";
                                    SetMarkAndComments(beamInstance, mark, elementComments);

                                    beamsCreated++;
                                }
                                catch (Exception ex)
                                {
                                    failureCount++;
                                    Log($"ERROR creating Y-beam at x={x}, y={y1}->{y2}, Level {storey}: {ex.Message}");
                                }
                            }
                        }
                    }
                    Log($"Beams generated: {beamsCreated} (expected: 310)");

                    // 3. Structural Walls (40 total: 4 panels per storey × 10 storeys)
                    var wallConfigs = new (string Tag, double X1, double Y1, double X2, double Y2)[]
                    {
                        ("WY1", 0.0, 5.0, 0.0, 10.0),
                        ("WY2", 20.0, 5.0, 20.0, 10.0),
                        ("WX1", 5.0, 0.0, 10.0, 0.0),
                        ("WX2", 10.0, 15.0, 15.0, 15.0)
                    };

                    for (int storey = 1; storey <= 10; storey++)
                    {
                        var baseLvl = levels[storey - 1];

                        foreach (var wc in wallConfigs)
                        {
                            try
                            {
                                var p1 = new XYZ(MToFt(wc.X1), MToFt(wc.Y1), baseLvl.Elevation);
                                var p2 = new XYZ(MToFt(wc.X2), MToFt(wc.Y2), baseLvl.Elevation);
                                var line = Line.CreateBound(p1, p2);

                                var wall = Wall.Create(
                                    doc,
                                    line,
                                    pcWallType!.Id,
                                    baseLvl.Id,
                                    MToFt(3.0),
                                    0.0,
                                    false,
                                    true);

                                string mark = $"PC-W-{wc.Tag}-S{storey}";
                                SetMarkAndComments(wall, mark, elementComments);

                                wallsCreated++;
                            }
                            catch (Exception ex)
                            {
                                failureCount++;
                                Log($"ERROR creating wall {wc.Tag} Storey {storey}: {ex.Message}");
                            }
                        }
                    }
                    Log($"Walls generated: {wallsCreated} (expected: 40)");

                    // 4. Floors (10 total: 1 per level 1..10)
                    for (int storey = 1; storey <= 10; storey++)
                    {
                        var lvl = levels[storey];

                        try
                        {
                            var loop = new CurveLoop();
                            var p1 = new XYZ(MToFt(0.0), MToFt(0.0), 0.0);
                            var p2 = new XYZ(MToFt(20.0), MToFt(0.0), 0.0);
                            var p3 = new XYZ(MToFt(20.0), MToFt(15.0), 0.0);
                            var p4 = new XYZ(MToFt(0.0), MToFt(15.0), 0.0);

                            loop.Append(Line.CreateBound(p1, p2));
                            loop.Append(Line.CreateBound(p2, p3));
                            loop.Append(Line.CreateBound(p3, p4));
                            loop.Append(Line.CreateBound(p4, p1));

                            var floor = Floor.Create(doc, new List<CurveLoop> { loop }, pcFloorType!.Id, lvl.Id);
                            var structParam = floor.get_Parameter(BuiltInParameter.FLOOR_PARAM_IS_STRUCTURAL);
                            structParam?.Set(1);

                            string mark = $"PC-S-L{storey}";
                            SetMarkAndComments(floor, mark, elementComments);

                            floorsCreated++;
                        }
                        catch (Exception ex)
                        {
                            failureCount++;
                            Log($"ERROR creating floor at Level {storey}: {ex.Message}");
                        }
                    }
                    Log($"Floors generated: {floorsCreated} (expected: 10)");

                    tx.Commit();
                }

                // -------------------------------------------------------------
                // Phase 4: Views Setup (3D View and Floor Plan Views)
                // -------------------------------------------------------------
                View3D? isometric3D = null;
                using (var tx = new Transaction(doc, "Create Views"))
                {
                    tx.Start();

                    var vftPlan = new FilteredElementCollector(doc)
                        .OfClass(typeof(ViewFamilyType))
                        .Cast<ViewFamilyType>()
                        .FirstOrDefault(v => v.ViewFamily == ViewFamily.StructuralPlan)
                        ?? new FilteredElementCollector(doc)
                        .OfClass(typeof(ViewFamilyType))
                        .Cast<ViewFamilyType>()
                        .FirstOrDefault(v => v.ViewFamily == ViewFamily.FloorPlan);

                    if (vftPlan != null)
                    {
                        for (int i = 0; i <= 10; i++)
                        {
                            var lvl = levels[i];
                            var existingPlan = new FilteredElementCollector(doc)
                                .OfClass(typeof(ViewPlan))
                                .Cast<ViewPlan>()
                                .FirstOrDefault(vp => vp.GenLevel != null && vp.GenLevel.Id == lvl.Id);

                            if (existingPlan == null)
                            {
                                try
                                {
                                    var vp = ViewPlan.Create(doc, vftPlan.Id, lvl.Id);
                                    vp.Name = lvl.Name;
                                }
                                catch
                                {
                                    // ignore name clash if view already exists
                                }
                            }
                        }
                    }

                    var vft3D = new FilteredElementCollector(doc)
                        .OfClass(typeof(ViewFamilyType))
                        .Cast<ViewFamilyType>()
                        .FirstOrDefault(v => v.ViewFamily == ViewFamily.ThreeDimensional);

                    if (vft3D != null)
                    {
                        isometric3D = View3D.CreateIsometric(doc, vft3D.Id);
                        isometric3D.Name = "BIM 3D";
                        isometric3D.DetailLevel = ViewDetailLevel.Fine;
                        isometric3D.DisplayStyle = DisplayStyle.Shading;
                        Log("Created 3D Isometric View 'BIM 3D' (Detail: Fine, DisplayStyle: Shading).");
                    }
                    else
                    {
                        Log("WARNING: Could not find ViewFamilyType for ThreeDimensional.");
                    }

                    tx.Commit();
                }

                // -------------------------------------------------------------
                // Summary of Created Elements
                // -------------------------------------------------------------
                Log("================================================================================");
                Log($"MODEL SUMMARY:");
                Log($"  Columns: {columnsCreated} / 200");
                Log($"  Beams:   {beamsCreated} / 310");
                Log($"  Walls:   {wallsCreated} / 40");
                Log($"  Floors:  {floorsCreated} / 10");
                Log($"  Total:   {columnsCreated + beamsCreated + wallsCreated + floorsCreated} / 560 elements");
                Log($"  Failures:{failureCount}");
                Log("================================================================================");

                // -------------------------------------------------------------
                // Phase 5: Save Project (.rvt)
                // -------------------------------------------------------------
                Log($"Saving project file to '{RvtPath}'...");
                var saveOpts = new SaveAsOptions { OverwriteExistingFile = true };
                doc.SaveAs(RvtPath, saveOpts);
                Log("Project document saved successfully.");

                // -------------------------------------------------------------
                // Phase 6: Export IFC
                // -------------------------------------------------------------
                Log($"Exporting IFC file to '{BimDir}\\{IfcFileName}'...");
                ExportIfc(doc, BimDir, IfcFileName);

                // -------------------------------------------------------------
                // Phase 7: Export 3D PNG View
                // -------------------------------------------------------------
                if (isometric3D != null)
                {
                    Log($"Exporting 3D PNG to '{PngPath}'...");
                    ExportPngView(doc, isometric3D, PngPath);
                }

                if (doc.IsModified)
                {
                    doc.Save();
                }

                return true;
            }
            finally
            {
                try
                {
                    Log("Closing document...");
                    doc.Close(false);
                    Log("Document closed successfully.");
                }
                catch (Exception ex)
                {
                    Log($"Exception closing document: {ex.Message}");
                }
            }
        }

        // =========================================================================
        // JOB 2: MEP Pipeline (PREFAB_BIM_JOB=mep)
        // Part A: Structural Model Shaft Opening Update
        // Part B: MEP Model Generation & Coordination
        // =========================================================================
        private static bool ExecuteMepPipeline(Autodesk.Revit.ApplicationServices.Application app)
        {
            Log("================================================================================");
            Log("Starting MEP Job Pipeline (Part A: Shaft Opening + Part B: MEP Model)...");
            Log("================================================================================");

            bool partASuccess = false;
            try
            {
                partASuccess = UpdateStructuralShaft(app);
            }
            catch (Exception ex)
            {
                Log($"ERROR in Part A (UpdateStructuralShaft): {ex}");
            }
            Log($"Part A (Structural Shaft Opening) Result: {(partASuccess ? "SUCCESS" : "FAILED")}");

            bool partBSuccess = false;
            try
            {
                partBSuccess = ExecuteMepGeneration(app);
            }
            catch (Exception ex)
            {
                Log($"ERROR in Part B (ExecuteMepGeneration): {ex}");
            }
            Log($"Part B (MEP Model Generation) Result: {(partBSuccess ? "SUCCESS" : "FAILED")}");

            return partBSuccess;
        }

        private static bool UpdateStructuralShaft(Autodesk.Revit.ApplicationServices.Application app)
        {
            Log("--------------------------------------------------------------------------------");
            Log("Part A: Opening structural model to add MEP shaft opening...");
            Log("--------------------------------------------------------------------------------");

            if (!File.Exists(RvtPath))
            {
                Log($"ERROR: Structural model file not found at '{RvtPath}'. Cannot add shaft opening.");
                return false;
            }

            Document? structDoc = null;
            try
            {
                Log($"Opening document: '{RvtPath}'");
                structDoc = app.OpenDocumentFile(RvtPath);
                if (structDoc == null)
                {
                    Log("ERROR: OpenDocumentFile returned null.");
                    return false;
                }

                var levels = new FilteredElementCollector(structDoc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .ToList();

                var bottomLevel = levels.FirstOrDefault(l => l.Name.Equals("Base", StringComparison.OrdinalIgnoreCase))
                    ?? levels.OrderBy(l => l.Elevation).FirstOrDefault();

                var topLevel = levels.FirstOrDefault(l => l.Name.Equals("Level 10", StringComparison.OrdinalIgnoreCase))
                    ?? levels.OrderByDescending(l => l.Elevation).FirstOrDefault();

                if (bottomLevel == null || topLevel == null)
                {
                    Log("ERROR: Bottom level ('Base') or top level ('Level 10') not found in structural document.");
                    return false;
                }

                Log($"Located levels: Bottom = '{bottomLevel.Name}' ({bottomLevel.Elevation:F2} ft), Top = '{topLevel.Name}' ({topLevel.Elevation:F2} ft)");

                const string shaftComments = "MEP service shaft; must be formed (cast-in) in precast slabs before casting";

                // Clean any pre-existing shaft opening with matching comments for idempotency
                using (var tx = new Transaction(structDoc, "Clean Existing Shaft Openings"))
                {
                    tx.Start();
                    var existingShafts = new FilteredElementCollector(structDoc)
                        .OfClass(typeof(Opening))
                        .Cast<Opening>()
                        .Where(o =>
                        {
                            var c = o.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)?.AsString()
                                    ?? o.LookupParameter("Comments")?.AsString();
                            return c != null && c.IndexOf("MEP service shaft", StringComparison.OrdinalIgnoreCase) >= 0;
                        })
                        .ToList();

                    foreach (var es in existingShafts)
                    {
                        try
                        {
                            structDoc.Delete(es.Id);
                            Log($"Deleted existing shaft opening Id {es.Id} prior to recreation.");
                        }
                        catch { }
                    }
                    tx.Commit();
                }

                // Rectangle x: 11.0–13.0 m, y: 6.0–7.5 m
                double zBottom = bottomLevel.Elevation;
                var p1 = new XYZ(MToFt(11.0), MToFt(6.0), zBottom);
                var p2 = new XYZ(MToFt(13.0), MToFt(6.0), zBottom);
                var p3 = new XYZ(MToFt(13.0), MToFt(7.5), zBottom);
                var p4 = new XYZ(MToFt(11.0), MToFt(7.5), zBottom);

                var curveArray = new CurveArray();
                curveArray.Append(Line.CreateBound(p1, p2));
                curveArray.Append(Line.CreateBound(p2, p3));
                curveArray.Append(Line.CreateBound(p3, p4));
                curveArray.Append(Line.CreateBound(p4, p1));

                Opening? shaftOpening = null;
                using (var tx = new Transaction(structDoc, "Create MEP Shaft Opening"))
                {
                    tx.Start();
                    shaftOpening = structDoc.Create.NewOpening(bottomLevel, topLevel, curveArray);
                    if (shaftOpening != null)
                    {
                        SetMarkAndComments(shaftOpening, "MEP-SHAFT-01", shaftComments);

                        var topOffParam = shaftOpening.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET)
                                          ?? shaftOpening.LookupParameter("Top Offset");
                        if (topOffParam != null && !topOffParam.IsReadOnly)
                        {
                            topOffParam.Set(MToFt(0.5)); // Ensure penetration through Level 10 top slab
                        }

                        var baseOffParam = shaftOpening.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET)
                                           ?? shaftOpening.LookupParameter("Base Offset");
                        if (baseOffParam != null && !baseOffParam.IsReadOnly)
                        {
                            baseOffParam.Set(0.0);
                        }

                        Log($"Shaft opening created successfully (Id: {shaftOpening.Id}) from '{bottomLevel.Name}' to '{topLevel.Name}'. Comments: '{shaftComments}'");
                    }
                    tx.Commit();
                }

                // Save (overwrite) the RVT
                Log($"Saving updated structural model to '{RvtPath}'...");
                try
                {
                    structDoc.Save();
                    Log("Saved with doc.Save().");
                }
                catch (Exception exSave)
                {
                    Log($"doc.Save() failed ({exSave.Message}). Attempting doc.SaveAs...");
                    structDoc.SaveAs(RvtPath, new SaveAsOptions { OverwriteExistingFile = true });
                    Log("Saved with doc.SaveAs().");
                }

                // Re-export IFC
                Log($"Re-exporting structural IFC to '{BimDir}\\{IfcFileName}'...");
                ExportIfc(structDoc, BimDir, IfcFileName);

                // Re-export 3D PNG
                var view3D = new FilteredElementCollector(structDoc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("BIM 3D", StringComparison.OrdinalIgnoreCase))
                    ?? new FilteredElementCollector(structDoc)
                    .OfClass(typeof(View3D))
                    .Cast<View3D>()
                    .FirstOrDefault(v => !v.IsTemplate);

                if (view3D != null)
                {
                    Log($"Re-exporting structural 3D PNG to '{PngPath}'...");
                    ExportPngView(structDoc, view3D, PngPath);
                }
                else
                {
                    Log("WARNING: No 3D view found in structural model for PNG re-export.");
                }

                if (structDoc.IsModified)
                {
                    structDoc.Save();
                }

                return true;
            }
            catch (Exception ex)
            {
                Log($"ERROR in UpdateStructuralShaft: {ex}");
                return false;
            }
            finally
            {
                if (structDoc != null)
                {
                    try
                    {
                        Log("Closing structural document...");
                        structDoc.Close(false);
                        Log("Structural document closed successfully.");
                    }
                    catch (Exception exClose)
                    {
                        Log($"Exception closing structural document: {exClose.Message}");
                    }
                }
            }
        }

        private static bool ExecuteMepGeneration(Autodesk.Revit.ApplicationServices.Application app)
        {
            Log("--------------------------------------------------------------------------------");
            Log("Part B: Generating MEP Model & System Components...");
            Log("--------------------------------------------------------------------------------");

            if (!File.Exists(MepTemplatePath))
            {
                Log($"ERROR: MEP template file not found at '{MepTemplatePath}'");
                return false;
            }

            Document? mepDoc = null;
            int pipesCreated = 0;
            int ductsCreated = 0;
            int cableTraysCreated = 0;
            int mepFailures = 0;
            bool linkSuccess = false;

            try
            {
                Log($"Creating new MEP project from template: '{MepTemplatePath}'...");
                mepDoc = app.NewProjectDocument(MepTemplatePath);
                if (mepDoc == null)
                {
                    Log("ERROR: Failed to create new MEP project from template.");
                    return false;
                }

                // -------------------------------------------------------------
                // B.1 Levels: Base (0.0) and Level 1..10 (3.0 m intervals)
                // -------------------------------------------------------------
                var levels = new Level[11];
                using (var tx = new Transaction(mepDoc, "Setup MEP Levels"))
                {
                    tx.Start();
                    var existingLevels = new FilteredElementCollector(mepDoc)
                        .OfClass(typeof(Level))
                        .Cast<Level>()
                        .ToList();

                    for (int i = 0; i < existingLevels.Count; i++)
                    {
                        existingLevels[i].Name = $"_tmp_mep_lvl_{Guid.NewGuid():N}";
                    }

                    for (int i = 0; i <= 10; i++)
                    {
                        string lvlName = (i == 0) ? "Base" : $"Level {i}";
                        double elevM = i * 3.0;
                        double elevFt = MToFt(elevM);

                        Level lvl;
                        if (i < existingLevels.Count)
                        {
                            lvl = existingLevels[i];
                            lvl.Elevation = elevFt;
                            lvl.Name = lvlName;
                        }
                        else
                        {
                            lvl = Level.Create(mepDoc, elevFt);
                            lvl.Name = lvlName;
                        }
                        levels[i] = lvl;
                        Log($"MEP Level [{i}]: '{lvl.Name}', Elevation = {elevM:F1} m ({elevFt:F3} ft)");
                    }

                    for (int i = 11; i < existingLevels.Count; i++)
                    {
                        try { mepDoc.Delete(existingLevels[i].Id); } catch { }
                    }
                    tx.Commit();
                }

                // -------------------------------------------------------------
                // B.2 Link the structural model (origin to origin)
                // -------------------------------------------------------------
                ElementId? linkInstanceId = null;
                if (File.Exists(RvtPath))
                {
                    try
                    {
                        using (var tx = new Transaction(mepDoc, "Link Structural Model"))
                        {
                            tx.Start();
                            var modelPath = ModelPathUtils.ConvertUserVisiblePathToModelPath(RvtPath);
                            var linkOptions = new RevitLinkOptions(false);
                            var loadResult = RevitLinkType.Create(mepDoc, modelPath, linkOptions);
                            var linkTypeId = loadResult.ElementId;

                            if (linkTypeId != null && linkTypeId != ElementId.InvalidElementId)
                            {
                                var linkInstance = RevitLinkInstance.Create(mepDoc, linkTypeId);
                                linkInstanceId = linkInstance.Id;
                                linkSuccess = true;
                                Log($"Linked structural model '{RvtPath}' successfully (LinkTypeId: {linkTypeId}, InstanceId: {linkInstance.Id}).");
                            }
                            else
                            {
                                Log($"WARNING: RevitLinkType.Create returned invalid ElementId: {loadResult.LoadResult}");
                            }
                            tx.Commit();
                        }
                    }
                    catch (Exception exLink)
                    {
                        Log($"ERROR linking structural model '{RvtPath}': {exLink.Message}");
                    }
                }
                else
                {
                    Log($"WARNING: Structural model '{RvtPath}' does not exist on disk. Skipping link.");
                }

                // -------------------------------------------------------------
                // B.3 Pick types by name with fallbacks and log chosen ones
                // -------------------------------------------------------------
                // 1. PipeType (first available)
                var pipeTypes = new FilteredElementCollector(mepDoc)
                    .OfClass(typeof(PipeType))
                    .Cast<PipeType>()
                    .ToList();
                var selectedPipeType = pipeTypes.FirstOrDefault();
                if (selectedPipeType == null)
                {
                    throw new InvalidOperationException("No PipeType found in MEP template.");
                }
                Log($"Selected PipeType: '{selectedPipeType.Name}' (Id: {selectedPipeType.Id})");

                // 2. PipingSystemTypes ("Domestic Cold Water" & "Sanitary")
                var pipingSysTypes = new FilteredElementCollector(mepDoc)
                    .OfClass(typeof(PipingSystemType))
                    .Cast<PipingSystemType>()
                    .ToList();

                var cwSysType = pipingSysTypes.FirstOrDefault(pst =>
                    pst.Name.IndexOf("Domestic Cold Water", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    pst.Name.IndexOf("Cold Water", StringComparison.OrdinalIgnoreCase) >= 0)
                    ?? pipingSysTypes.FirstOrDefault(pst => pst.SystemClassification == MEPSystemClassification.DomesticColdWater)
                    ?? pipingSysTypes.FirstOrDefault();

                if (cwSysType == null)
                {
                    throw new InvalidOperationException("No PipingSystemType found for Domestic Cold Water.");
                }
                Log($"Selected Domestic Cold Water PipingSystemType: '{cwSysType.Name}' (Classification: {cwSysType.SystemClassification}, Id: {cwSysType.Id})");

                var sanSysType = pipingSysTypes.FirstOrDefault(pst =>
                    pst.Name.IndexOf("Sanitary", StringComparison.OrdinalIgnoreCase) >= 0)
                    ?? pipingSysTypes.FirstOrDefault(pst => pst.SystemClassification == MEPSystemClassification.Sanitary)
                    ?? pipingSysTypes.FirstOrDefault();

                if (sanSysType == null)
                {
                    throw new InvalidOperationException("No PipingSystemType found for Sanitary.");
                }
                Log($"Selected Sanitary PipingSystemType: '{sanSysType.Name}' (Classification: {sanSysType.SystemClassification}, Id: {sanSysType.Id})");

                // 3. Rectangular DuctType
                var ductTypes = new FilteredElementCollector(mepDoc)
                    .OfClass(typeof(DuctType))
                    .Cast<DuctType>()
                    .ToList();

                var rectDuctType = ductTypes.FirstOrDefault(dt => dt.Shape == ConnectorProfileType.Rectangular)
                    ?? ductTypes.FirstOrDefault(dt => dt.Name.IndexOf("Rectangular", StringComparison.OrdinalIgnoreCase) >= 0)
                    ?? ductTypes.FirstOrDefault();

                if (rectDuctType == null)
                {
                    throw new InvalidOperationException("No rectangular DuctType found in MEP template.");
                }
                Log($"Selected Rectangular DuctType: '{rectDuctType.Name}' (Shape: {rectDuctType.Shape}, Id: {rectDuctType.Id})");

                // 4. MechanicalSystemType "Exhaust Air"
                var mechSysTypes = new FilteredElementCollector(mepDoc)
                    .OfClass(typeof(MechanicalSystemType))
                    .Cast<MechanicalSystemType>()
                    .ToList();

                var exhSysType = mechSysTypes.FirstOrDefault(mst =>
                    mst.Name.IndexOf("Exhaust Air", StringComparison.OrdinalIgnoreCase) >= 0 ||
                    mst.Name.IndexOf("Exhaust", StringComparison.OrdinalIgnoreCase) >= 0)
                    ?? mechSysTypes.FirstOrDefault(mst => mst.SystemClassification == MEPSystemClassification.ExhaustAir)
                    ?? mechSysTypes.FirstOrDefault();

                if (exhSysType == null)
                {
                    throw new InvalidOperationException("No MechanicalSystemType found for Exhaust Air.");
                }
                Log($"Selected Exhaust Air MechanicalSystemType: '{exhSysType.Name}' (Classification: {exhSysType.SystemClassification}, Id: {exhSysType.Id})");

                // 5. CableTrayType (first available)
                var cableTrayTypes = new FilteredElementCollector(mepDoc)
                    .OfClass(typeof(CableTrayType))
                    .Cast<CableTrayType>()
                    .ToList();

                var selectedTrayType = cableTrayTypes.FirstOrDefault();
                if (selectedTrayType == null)
                {
                    throw new InvalidOperationException("No CableTrayType found in MEP template.");
                }
                Log($"Selected CableTrayType: '{selectedTrayType.Name}' (Id: {selectedTrayType.Id})");

                // -------------------------------------------------------------
                // B.4 Vertical Risers in shaft from z = 0.0 to z = 31.0 m (level "Base")
                // -------------------------------------------------------------
                var baseLevel = levels[0];
                using (var tx = new Transaction(mepDoc, "Create MEP Vertical Risers"))
                {
                    tx.Start();

                    double z0 = MToFt(0.0);
                    double z31 = MToFt(31.0);

                    // 1. Pipe DN50 Domestic Cold Water at (11.3, 6.3)
                    try
                    {
                        var p1 = new XYZ(MToFt(11.3), MToFt(6.3), z0);
                        var p2 = new XYZ(MToFt(11.3), MToFt(6.3), z31);
                        var pipe = Pipe.Create(mepDoc, cwSysType.Id, selectedPipeType.Id, baseLevel.Id, p1, p2);
                        SetPipeDiameter(pipe, 50.0);
                        SetMarkAndComments(pipe, "MEP-Pipe-CW-Riser", "Domestic Cold Water Riser");
                        pipesCreated++;
                        Log($"Created Pipe DN50 CW Riser (Id: {pipe.Id})");
                    }
                    catch (Exception ex)
                    {
                        mepFailures++;
                        Log($"ERROR creating CW riser: {ex.Message}");
                    }

                    // 2. Pipe DN100 Sanitary at (11.8, 6.3)
                    try
                    {
                        var p1 = new XYZ(MToFt(11.8), MToFt(6.3), z0);
                        var p2 = new XYZ(MToFt(11.8), MToFt(6.3), z31);
                        var pipe = Pipe.Create(mepDoc, sanSysType.Id, selectedPipeType.Id, baseLevel.Id, p1, p2);
                        SetPipeDiameter(pipe, 100.0);
                        SetMarkAndComments(pipe, "MEP-Pipe-San-Riser", "Sanitary Soil/Waste Riser");
                        pipesCreated++;
                        Log($"Created Pipe DN100 Sanitary Riser (Id: {pipe.Id})");
                    }
                    catch (Exception ex)
                    {
                        mepFailures++;
                        Log($"ERROR creating Sanitary riser: {ex.Message}");
                    }

                    // 3. Pipe DN100 Sanitary (rainwater/vent stack) at (12.3, 6.3) — set Comments "Rainwater/vent stack"
                    try
                    {
                        var p1 = new XYZ(MToFt(12.3), MToFt(6.3), z0);
                        var p2 = new XYZ(MToFt(12.3), MToFt(6.3), z31);
                        var pipe = Pipe.Create(mepDoc, sanSysType.Id, selectedPipeType.Id, baseLevel.Id, p1, p2);
                        SetPipeDiameter(pipe, 100.0);
                        SetMarkAndComments(pipe, "MEP-Pipe-Vent-Riser", "Rainwater/vent stack");
                        pipesCreated++;
                        Log($"Created Pipe DN100 Rainwater/Vent Stack Riser (Id: {pipe.Id})");
                    }
                    catch (Exception ex)
                    {
                        mepFailures++;
                        Log($"ERROR creating Rainwater/vent stack riser: {ex.Message}");
                    }

                    // 4. Duct 400x250 Exhaust Air at (11.6, 7.1)
                    try
                    {
                        var p1 = new XYZ(MToFt(11.6), MToFt(7.1), z0);
                        var p2 = new XYZ(MToFt(11.6), MToFt(7.1), z31);
                        var duct = Duct.Create(mepDoc, exhSysType.Id, rectDuctType.Id, baseLevel.Id, p1, p2);
                        SetDuctSize(duct, 400.0, 250.0);
                        SetMarkAndComments(duct, "MEP-Duct-Exhaust-Riser", "Exhaust Air Riser 400x250");
                        ductsCreated++;
                        Log($"Created Duct 400x250 Exhaust Air Riser (Id: {duct.Id})");
                    }
                    catch (Exception ex)
                    {
                        mepFailures++;
                        Log($"ERROR creating Exhaust Air duct riser: {ex.Message}");
                    }

                    // 5. Cable tray 300x100 at (12.6, 7.1)
                    try
                    {
                        var p1 = new XYZ(MToFt(12.6), MToFt(7.1), z0);
                        var p2 = new XYZ(MToFt(12.6), MToFt(7.1), z31);
                        CableTray? tray = null;
                        try
                        {
                            tray = CableTray.Create(mepDoc, selectedTrayType.Id, p1, p2, baseLevel.Id);
                        }
                        catch (Exception exTrayVert)
                        {
                            Log($"Vertical CableTray.Create direct attempt note: {exTrayVert.Message}. Trying with micro offset (1 mm)...");
                            var p2Adj = new XYZ(MToFt(12.601), MToFt(7.1), z31);
                            tray = CableTray.Create(mepDoc, selectedTrayType.Id, p1, p2Adj, baseLevel.Id);
                        }

                        if (tray != null)
                        {
                            SetCableTraySize(tray, 300.0, 100.0);
                            SetMarkAndComments(tray, "MEP-CableTray-Riser", "Main Electrical / Data Cable Tray Riser");
                            cableTraysCreated++;
                            Log($"Created Cable Tray 300x100 Riser (Id: {tray.Id})");
                        }
                    }
                    catch (Exception ex)
                    {
                        mepFailures++;
                        Log($"ERROR creating Cable Tray riser: {ex.Message}");
                    }

                    tx.Commit();
                }

                // -------------------------------------------------------------
                // B.5 Per floor i = 1..10
                // reference level = "Level i-1" for i=1 -> "Base"
                // elevation zi = 3.0*i - 0.65 m
                // -------------------------------------------------------------
                for (int i = 1; i <= 10; i++)
                {
                    var refLevel = levels[i - 1];
                    double zi = 3.0 * i - 0.65;
                    double zFt = MToFt(zi);

                    using (var tx = new Transaction(mepDoc, $"Create MEP Floor {i} Branches"))
                    {
                        tx.Start();

                        // 1. Cold-water branch DN25: from (11.3, 6.3, zi) to (7.5, 6.3, zi)
                        try
                        {
                            var p1 = new XYZ(MToFt(11.3), MToFt(6.3), zFt);
                            var p2 = new XYZ(MToFt(7.5), MToFt(6.3), zFt);
                            var pipe = Pipe.Create(mepDoc, cwSysType.Id, selectedPipeType.Id, refLevel.Id, p1, p2);
                            SetPipeDiameter(pipe, 25.0);
                            SetMarkAndComments(pipe, $"MEP-Pipe-CW-L{i}-1", "Domestic Cold Water Branch 1");
                            pipesCreated++;
                        }
                        catch (Exception ex)
                        {
                            mepFailures++;
                            Log($"ERROR creating CW branch 1 at Level {i}: {ex.Message}");
                        }

                        // 2. Cold-water branch DN25: from (11.3, 6.3, zi) to (15.5, 6.3, zi)
                        try
                        {
                            var p1 = new XYZ(MToFt(11.3), MToFt(6.3), zFt);
                            var p2 = new XYZ(MToFt(15.5), MToFt(6.3), zFt);
                            var pipe = Pipe.Create(mepDoc, cwSysType.Id, selectedPipeType.Id, refLevel.Id, p1, p2);
                            SetPipeDiameter(pipe, 25.0);
                            SetMarkAndComments(pipe, $"MEP-Pipe-CW-L{i}-2", "Domestic Cold Water Branch 2");
                            pipesCreated++;
                        }
                        catch (Exception ex)
                        {
                            mepFailures++;
                            Log($"ERROR creating CW branch 2 at Level {i}: {ex.Message}");
                        }

                        // 3. Sanitary branch DN100 at zi - 0.15: from (11.8, 6.3) to (7.5, 6.3)
                        try
                        {
                            double zSanFt = MToFt(zi - 0.15);
                            var p1 = new XYZ(MToFt(11.8), MToFt(6.3), zSanFt);
                            var p2 = new XYZ(MToFt(7.5), MToFt(6.3), zSanFt);
                            var pipe = Pipe.Create(mepDoc, sanSysType.Id, selectedPipeType.Id, refLevel.Id, p1, p2);
                            SetPipeDiameter(pipe, 100.0);
                            SetMarkAndComments(pipe, $"MEP-Pipe-San-L{i}-1", "Sanitary Branch");
                            pipesCreated++;
                        }
                        catch (Exception ex)
                        {
                            mepFailures++;
                            Log($"ERROR creating Sanitary branch at Level {i}: {ex.Message}");
                        }

                        // 4. Exhaust duct branch 200x150 at zi: from (11.6, 7.1) to (6.0, 7.1)
                        try
                        {
                            var p1 = new XYZ(MToFt(11.6), MToFt(7.1), zFt);
                            var p2 = new XYZ(MToFt(6.0), MToFt(7.1), zFt);
                            var duct = Duct.Create(mepDoc, exhSysType.Id, rectDuctType.Id, refLevel.Id, p1, p2);
                            SetDuctSize(duct, 200.0, 150.0);
                            SetMarkAndComments(duct, $"MEP-Duct-Exhaust-L{i}-1", "Exhaust Duct Branch 200x150");
                            ductsCreated++;
                        }
                        catch (Exception ex)
                        {
                            mepFailures++;
                            Log($"ERROR creating Exhaust duct branch at Level {i}: {ex.Message}");
                        }

                        // 5. Cable tray 200x50 at zi + 0.05: from (12.6, 7.1) to (18.0, 7.1)
                        try
                        {
                            double zTrayFt = MToFt(zi + 0.05);
                            var p1 = new XYZ(MToFt(12.6), MToFt(7.1), zTrayFt);
                            var p2 = new XYZ(MToFt(18.0), MToFt(7.1), zTrayFt);
                            var tray = CableTray.Create(mepDoc, selectedTrayType.Id, p1, p2, refLevel.Id);
                            SetCableTraySize(tray, 200.0, 50.0);
                            SetMarkAndComments(tray, $"MEP-CableTray-L{i}-1", "Cable Tray Branch 1 (East)");
                            cableTraysCreated++;
                        }
                        catch (Exception ex)
                        {
                            mepFailures++;
                            Log($"ERROR creating Cable tray branch 1 at Level {i}: {ex.Message}");
                        }

                        // 6. Cable tray 200x50 at zi + 0.05: from (12.6, 7.1) to (2.0, 7.1)
                        try
                        {
                            double zTrayFt = MToFt(zi + 0.05);
                            var p1 = new XYZ(MToFt(12.6), MToFt(7.1), zTrayFt);
                            var p2 = new XYZ(MToFt(2.0), MToFt(7.1), zTrayFt);
                            var tray = CableTray.Create(mepDoc, selectedTrayType.Id, p1, p2, refLevel.Id);
                            SetCableTraySize(tray, 200.0, 50.0);
                            SetMarkAndComments(tray, $"MEP-CableTray-L{i}-2", "Cable Tray Branch 2 (West)");
                            cableTraysCreated++;
                        }
                        catch (Exception ex)
                        {
                            mepFailures++;
                            Log($"ERROR creating Cable tray branch 2 at Level {i}: {ex.Message}");
                        }

                        tx.Commit();
                    }
                }

                // -------------------------------------------------------------
                // B.6 Create 3D isometric view "MEP 3D"
                // -------------------------------------------------------------
                View3D? mep3DView = null;
                using (var tx = new Transaction(mepDoc, "Create MEP 3D View"))
                {
                    tx.Start();

                    var existingView = new FilteredElementCollector(mepDoc)
                        .OfClass(typeof(View3D))
                        .Cast<View3D>()
                        .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("MEP 3D", StringComparison.OrdinalIgnoreCase));

                    if (existingView != null)
                    {
                        try { existingView.Name = $"_tmp_mep3d_{Guid.NewGuid():N}"; } catch { }
                    }

                    var vft3D = new FilteredElementCollector(mepDoc)
                        .OfClass(typeof(ViewFamilyType))
                        .Cast<ViewFamilyType>()
                        .FirstOrDefault(v => v.ViewFamily == ViewFamily.ThreeDimensional);

                    if (vft3D != null)
                    {
                        mep3DView = View3D.CreateIsometric(mepDoc, vft3D.Id);
                        mep3DView.Name = "MEP 3D";
                        mep3DView.DetailLevel = ViewDetailLevel.Fine;
                        mep3DView.DisplayStyle = DisplayStyle.Shading;

                        if (linkInstanceId != null && linkInstanceId != ElementId.InvalidElementId)
                        {
                            try
                            {
                                var ogs = new OverrideGraphicSettings();
                                ogs.SetHalftone(true);
                                mep3DView.SetElementOverrides(linkInstanceId, ogs);
                                Log($"Set linked structural model (Id: {linkInstanceId}) to halftone in 'MEP 3D'.");
                            }
                            catch (Exception exOgs)
                            {
                                Log($"Note: Could not set link halftone overrides in 3D view: {exOgs.Message}");
                            }
                        }
                        Log("Created 3D Isometric View 'MEP 3D' (Detail: Fine, DisplayStyle: Shading).");
                    }
                    else
                    {
                        Log("WARNING: Could not find ViewFamilyType for ThreeDimensional in MEP template.");
                    }
                    tx.Commit();
                }

                // -------------------------------------------------------------
                // B.8 Log counts of pipes, ducts, cable trays, link status
                // -------------------------------------------------------------
                Log("================================================================================");
                Log("MEP MODEL SUMMARY:");
                Log($"  Pipes created:       {pipesCreated} (expected: 33 = 3 risers + 30 branches)");
                Log($"  Ducts created:       {ductsCreated} (expected: 11 = 1 riser + 10 branches)");
                Log($"  Cable trays created: {cableTraysCreated} (expected: 21 = 1 riser + 20 branches)");
                Log($"  Total MEP elements:  {pipesCreated + ductsCreated + cableTraysCreated} / 65");
                Log($"  Failures:            {mepFailures}");
                Log($"  Link status:         {(linkSuccess ? "Linked successfully (halftone in 3D view)" : "Link failed or skipped")}");
                Log("================================================================================");

                // -------------------------------------------------------------
                // B.7 Save as BIM/Prefab_RCC_10storey_MEP.rvt (overwrite)
                // -------------------------------------------------------------
                Log($"Saving MEP model to '{MepRvtPath}'...");
                var saveOpts = new SaveAsOptions { OverwriteExistingFile = true };
                mepDoc.SaveAs(MepRvtPath, saveOpts);
                Log("MEP model saved successfully.");

                // Export IFC BIM/Prefab_RCC_10storey_MEP.ifc
                Log($"Exporting MEP IFC file to '{BimDir}\\{MepIfcFileName}'...");
                ExportIfc(mepDoc, BimDir, MepIfcFileName);

                // Export PNG BIM/Prefab_RCC_10storey_MEP_3D.png (1600 px)
                if (mep3DView != null)
                {
                    Log($"Exporting MEP 3D PNG to '{MepPngPath}'...");
                    ExportPngView(mepDoc, mep3DView, MepPngPath);
                }
                else
                {
                    Log("WARNING: No 3D view available for MEP PNG export.");
                }

                if (mepDoc.IsModified)
                {
                    mepDoc.Save();
                }

                return true;
            }
            catch (Exception ex)
            {
                Log($"FATAL ERROR in ExecuteMepGeneration: {ex}");
                return false;
            }
            finally
            {
                if (mepDoc != null)
                {
                    try
                    {
                        Log("Closing MEP document...");
                        mepDoc.Close(false);
                        Log("MEP document closed successfully.");
                    }
                    catch (Exception exClose)
                    {
                        Log($"Exception closing MEP document: {exClose.Message}");
                    }
                }
            }
        }

        // =========================================================================
        // Helper Methods
        // =========================================================================
        private static void SetPipeDiameter(Pipe pipe, double diameterMm)
        {
            try
            {
                double diamFt = MmToFt(diameterMm);
                var p = pipe.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM)
                    ?? pipe.LookupParameter("Diameter");
                if (p != null && !p.IsReadOnly)
                {
                    bool ok = p.Set(diamFt);
                    Log($"Pipe {pipe.Id}: Set diameter = {diameterMm} mm ({diamFt:F4} ft) [Success: {ok}]");
                }
                else
                {
                    Log($"WARNING: RBS_PIPE_DIAMETER_PARAM not writable on Pipe {pipe.Id}");
                }
            }
            catch (Exception ex)
            {
                Log($"WARNING: Failed setting diameter on Pipe {pipe.Id}: {ex.Message}");
            }
        }

        private static void SetDuctSize(Duct duct, double widthMm, double heightMm)
        {
            try
            {
                double wFt = MmToFt(widthMm);
                double hFt = MmToFt(heightMm);

                var pw = duct.get_Parameter(BuiltInParameter.RBS_CURVE_WIDTH_PARAM)
                    ?? duct.LookupParameter("Width");
                bool wOk = false;
                if (pw != null && !pw.IsReadOnly)
                {
                    wOk = pw.Set(wFt);
                }

                var ph = duct.get_Parameter(BuiltInParameter.RBS_CURVE_HEIGHT_PARAM)
                    ?? duct.LookupParameter("Height");
                bool hOk = false;
                if (ph != null && !ph.IsReadOnly)
                {
                    hOk = ph.Set(hFt);
                }

                Log($"Duct {duct.Id}: Set size = {widthMm}x{heightMm} mm [Width set: {wOk}, Height set: {hOk}]");
            }
            catch (Exception ex)
            {
                Log($"WARNING: Failed setting size on Duct {duct.Id}: {ex.Message}");
            }
        }

        private static void SetCableTraySize(CableTray tray, double widthMm, double heightMm)
        {
            try
            {
                double wFt = MmToFt(widthMm);
                double hFt = MmToFt(heightMm);
                bool wSet = false;
                bool hSet = false;

                var pw = tray.get_Parameter(BuiltInParameter.RBS_CABLETRAY_WIDTH_PARAM)
                    ?? tray.get_Parameter(BuiltInParameter.RBS_CURVE_WIDTH_PARAM)
                    ?? tray.LookupParameter("Width");

                if (pw != null && !pw.IsReadOnly)
                {
                    wSet = pw.Set(wFt);
                }

                var ph = tray.get_Parameter(BuiltInParameter.RBS_CABLETRAY_HEIGHT_PARAM)
                    ?? tray.get_Parameter(BuiltInParameter.RBS_CURVE_HEIGHT_PARAM)
                    ?? tray.LookupParameter("Height");

                if (ph != null && !ph.IsReadOnly)
                {
                    hSet = ph.Set(hFt);
                }

                Log($"CableTray {tray.Id}: Set size = {widthMm}x{heightMm} mm [Width set: {wSet}, Height set: {hSet}]");
            }
            catch (Exception ex)
            {
                Log($"WARNING: Failed setting size on CableTray {tray.Id}: {ex.Message}");
            }
        }

        // =========================================================================
        // JOB 3: Substructure Pipeline (PREFAB_BIM_JOB=sub)
        // Adds pile foundation (pile caps & bored piles) and grade beams
        // =========================================================================
        private static bool ExecuteSubPipeline(Autodesk.Revit.ApplicationServices.Application app)
        {
            Log("================================================================================");
            Log("Starting Substructure Job Pipeline (PREFAB_BIM_JOB=sub)...");
            Log("================================================================================");

            if (!File.Exists(RvtPath))
            {
                Log($"ERROR: Structural model file not found at '{RvtPath}'. Cannot add substructure.");
                return false;
            }

            // 1. Locate and parse pile_design JSON
            string jsonPath = PileDesignJsonPath;
            if (!File.Exists(jsonPath))
            {
                var altPath = Path.Combine(Directory.GetCurrentDirectory(), "Paper2_Structural", "analysis", "2_Precast", "reactions_M2_fix600", "pile_design_Qa1307.json");
                if (File.Exists(altPath))
                {
                    jsonPath = altPath;
                }
                else
                {
                    Log($"ERROR: Pile design JSON not found at '{jsonPath}' or '{altPath}'.");
                    return false;
                }
            }

            Log($"Reading pile design JSON from '{jsonPath}'...");
            PileDesignData? designData;
            try
            {
                string jsonText = File.ReadAllText(jsonPath);
                var jsonOptions = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                designData = JsonSerializer.Deserialize<PileDesignData>(jsonText, jsonOptions);
                if (designData == null || designData.Caps == null || designData.Caps.Count == 0)
                {
                    Log("ERROR: Deserialized pile design data is null or contains no caps.");
                    return false;
                }
                Log($"Successfully parsed pile design JSON: total_piles = {designData.TotalPiles}, caps count = {designData.Caps.Count}");
            }
            catch (Exception exJson)
            {
                Log($"ERROR parsing pile design JSON: {exJson}");
                return false;
            }

            Document? doc = null;
            int capsCreated = 0;
            int pilesCreated = 0;
            int gradeBeamsCreated = 0;
            int failureCount = 0;

            try
            {
                Log($"Opening structural model document: '{RvtPath}'");
                doc = app.OpenDocumentFile(RvtPath);
                if (doc == null)
                {
                    Log("ERROR: OpenDocumentFile returned null.");
                    return false;
                }

                // Locate Base level
                var levels = new FilteredElementCollector(doc)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .ToList();

                var baseLevel = levels.FirstOrDefault(l => l.Name.Equals("Base", StringComparison.OrdinalIgnoreCase))
                    ?? levels.OrderBy(l => l.Elevation).FirstOrDefault();

                if (baseLevel == null)
                {
                    Log("ERROR: Base level not found in structural model.");
                    return false;
                }
                Log($"Located Base level: '{baseLevel.Name}', Elevation = {baseLevel.Elevation:F3} ft ({UnitUtils.ConvertFromInternalUnits(baseLevel.Elevation, UnitTypeId.Meters):F2} m)");

                // Locate concrete material
                var concreteMaterial = new FilteredElementCollector(doc)
                    .OfClass(typeof(Material))
                    .Cast<Material>()
                    .FirstOrDefault(m => m.Name.Equals("Concrete C28 (precast)", StringComparison.OrdinalIgnoreCase));

                if (concreteMaterial != null)
                {
                    Log($"Found material '{concreteMaterial.Name}' (Id: {concreteMaterial.Id}).");
                }
                else
                {
                    Log("WARNING: Material 'Concrete C28 (precast)' not found in document. Searching for any Concrete material...");
                    concreteMaterial = new FilteredElementCollector(doc)
                        .OfClass(typeof(Material))
                        .Cast<Material>()
                        .FirstOrDefault(m => m.Name.Contains("Concrete", StringComparison.OrdinalIgnoreCase));
                    if (concreteMaterial != null)
                    {
                        Log($"Using fallback material '{concreteMaterial.Name}' (Id: {concreteMaterial.Id}).");
                    }
                }

                // -------------------------------------------------------------
                // Phase 1: Clean up previously created elements (Comments start with "SUB:")
                // -------------------------------------------------------------
                using (var tx = new Transaction(doc, "Delete Previous Substructure Elements"))
                {
                    tx.Start();
                    var prevElements = new FilteredElementCollector(doc)
                        .WhereElementIsNotElementType()
                        .Where(e =>
                        {
                            var c = e.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)?.AsString()
                                    ?? e.LookupParameter("Comments")?.AsString();
                            return c != null && c.StartsWith("SUB:", StringComparison.OrdinalIgnoreCase);
                        })
                        .Select(e => e.Id)
                        .ToList();

                    if (prevElements.Count > 0)
                    {
                        Log($"Found {prevElements.Count} previous SUB elements to delete for clean re-run.");
                        foreach (var id in prevElements)
                        {
                            try
                            {
                                doc.Delete(id);
                            }
                            catch (Exception exDel)
                            {
                                Log($"Warning deleting element Id {id}: {exDel.Message}");
                            }
                        }
                        Log($"Deleted {prevElements.Count} previous SUB elements.");
                    }
                    else
                    {
                        Log("No previous SUB elements found to delete.");
                    }
                    tx.Commit();
                }

                // -------------------------------------------------------------
                // Phase 2: Prepare Types (Grade Beam & Isolated Footing Symbols)
                // -------------------------------------------------------------
                FamilySymbol? symGradeBeam = null;
                var capSymbolsBySize = new Dictionary<string, FamilySymbol>();

                using (var tx = new Transaction(doc, "Prepare Substructure Types"))
                {
                    tx.Start();

                    var matId = concreteMaterial?.Id ?? ElementId.InvalidElementId;

                    // 1. Grade beam symbol: "GB 300x600"
                    var beamSymbols = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_StructuralFraming)
                        .OfClass(typeof(FamilySymbol))
                        .Cast<FamilySymbol>()
                        .ToList();

                    var baseBeamSymbol = beamSymbols.FirstOrDefault(s =>
                        (s.FamilyName.Contains("Concrete", StringComparison.OrdinalIgnoreCase) || s.Name.Contains("Concrete", StringComparison.OrdinalIgnoreCase)) &&
                        (s.FamilyName.Contains("Rect", StringComparison.OrdinalIgnoreCase) || s.Name.Contains("Rect", StringComparison.OrdinalIgnoreCase)))
                        ?? beamSymbols.FirstOrDefault();

                    if (baseBeamSymbol != null)
                    {
                        symGradeBeam = GetOrCreateFamilySymbol(baseBeamSymbol, "GB 300x600");
                        SetDimensionParameters(symGradeBeam, MToFt(0.3), MToFt(0.6), matId, "GB 300x600");
                        Log($"Prepared grade beam symbol 'GB 300x600' from '{baseBeamSymbol.FamilyName}'.");
                    }
                    else
                    {
                        Log("WARNING: No base framing symbol found for grade beams.");
                    }

                    // 2. Foundation Family Symbols for Pile Caps (OST_StructuralFoundation)
                    var foundationSymbols = new FilteredElementCollector(doc)
                        .OfCategory(BuiltInCategory.OST_StructuralFoundation)
                        .OfClass(typeof(FamilySymbol))
                        .Cast<FamilySymbol>()
                        .ToList();

                    Log($"Found {foundationSymbols.Count} structural foundation symbols in document.");
                    foreach (var fs in foundationSymbols)
                    {
                        Log($"  Foundation Symbol: Family='{fs.FamilyName}', Name='{fs.Name}'");
                    }

                    var baseFootingSymbol = foundationSymbols.FirstOrDefault(s =>
                        (s.FamilyName.Contains("Footing", StringComparison.OrdinalIgnoreCase) || s.Name.Contains("Footing", StringComparison.OrdinalIgnoreCase)) &&
                        (s.FamilyName.Contains("Rect", StringComparison.OrdinalIgnoreCase) || s.Name.Contains("Rect", StringComparison.OrdinalIgnoreCase)));

                    if (baseFootingSymbol != null)
                    {
                        Log($"Found base footing symbol: '{baseFootingSymbol.FamilyName}' : '{baseFootingSymbol.Name}'");

                        var distinctSizes = designData.Caps
                            .Select(c => (Lx: c.Lx, Ly: c.Ly, Depth: c.Depth))
                            .Distinct()
                            .ToList();

                        foreach (var size in distinctSizes)
                        {
                            string typeName = $"PC-CAP {FormatDimension(size.Lx)}x{FormatDimension(size.Ly)}x{FormatDimension(size.Depth)}";
                            try
                            {
                                var capSym = GetOrCreateFamilySymbol(baseFootingSymbol, typeName);
                                if (TrySetFootingDimensions(capSym, MToFt(size.Lx), MToFt(size.Ly), MToFt(size.Depth), matId, out string loggedDetails))
                                {
                                    capSymbolsBySize[typeName] = capSym;
                                    Log($"Configured footing type '{typeName}': {loggedDetails}");
                                }
                                else
                                {
                                    Log($"Failed to configure all dimensions on footing type '{typeName}'. Will fall back to DirectShape for this size.");
                                }
                            }
                            catch (Exception exSym)
                            {
                                Log($"Exception preparing footing type '{typeName}': {exSym.Message}. Will fall back to DirectShape.");
                            }
                        }
                    }
                    else
                    {
                        Log("No isolated rectangular footing family found in template/document. Will use DirectShape fallback for all pile caps.");
                    }

                    tx.Commit();
                }

                // -------------------------------------------------------------
                // Phase 3: Create Pile Caps and Bored Piles
                // -------------------------------------------------------------
                using (var tx = new Transaction(doc, "Generate Pile Caps and Piles"))
                {
                    tx.Start();

                    foreach (var cap in designData.Caps)
                    {
                        double cx = cap.X;
                        double cy = cap.Y;
                        double lx = cap.Lx;
                        double ly = cap.Ly;
                        double depth = cap.Depth;
                        int n = cap.N;
                        string gridName = GetGridName(cx, cy);

                        // --- 2. Pile Cap Creation ---
                        bool capPlaced = false;
                        string typeName = $"PC-CAP {FormatDimension(lx)}x{FormatDimension(ly)}x{FormatDimension(depth)}";

                        if (capSymbolsBySize.TryGetValue(typeName, out var footingSym) && footingSym != null)
                        {
                            try
                            {
                                var pt = new XYZ(MToFt(cx), MToFt(cy), baseLevel.Elevation);
                                var capInstance = doc.Create.NewFamilyInstance(pt, footingSym, baseLevel, StructuralType.Footing);

                                // Adjust elevation offset so top is at 0.0
                                var bbox = capInstance.get_BoundingBox(null);
                                if (bbox != null)
                                {
                                    double zTop = bbox.Max.Z;
                                    double deltaZ = 0.0 - zTop;
                                    if (Math.Abs(deltaZ) > 0.001)
                                    {
                                        var offParam = capInstance.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)
                                                       ?? capInstance.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)
                                                       ?? capInstance.LookupParameter("Offset")
                                                       ?? capInstance.LookupParameter("Height Offset From Level");
                                        if (offParam != null && !offParam.IsReadOnly)
                                        {
                                            offParam.Set(offParam.AsDouble() + deltaZ);
                                        }
                                        else
                                        {
                                            ElementTransformUtils.MoveElement(doc, capInstance.Id, new XYZ(0, 0, deltaZ));
                                        }
                                    }
                                }

                                string mark = $"SUB-CAP-{gridName}";
                                string comments = $"SUB: pile cap, {n} piles";
                                SetMarkAndComments(capInstance, mark, comments);

                                capsCreated++;
                                capPlaced = true;
                                Log($"Created FamilyInstance pile cap '{mark}' at ({cx:F1},{cy:F1}), size {lx}x{ly}x{depth} m, type '{typeName}'.");
                            }
                            catch (Exception exFam)
                            {
                                Log($"Warning placing FamilyInstance cap at ({cx:F1},{cy:F1}): {exFam.Message}. Falling back to DirectShape...");
                            }
                        }

                        if (!capPlaced)
                        {
                            try
                            {
                                var dsCap = CreatePileCapDirectShape(doc, cx, cy, lx, ly, depth, concreteMaterial, gridName, n);
                                capsCreated++;
                                Log($"Created DirectShape pile cap 'SUB-CAP-{gridName}' at ({cx:F1},{cy:F1}), size {lx}x{ly}x{depth} m.");
                            }
                            catch (Exception exDs)
                            {
                                failureCount++;
                                Log($"ERROR creating DirectShape pile cap at ({cx:F1},{cy:F1}): {exDs.Message}");
                            }
                        }

                        // --- 3. Bored Piles Creation ---
                        var pileOffsets = GetPileOffsets(n);
                        for (int pi = 0; pi < pileOffsets.Count; pi++)
                        {
                            int pileK = pi + 1;
                            double px = cx + pileOffsets[pi].dx;
                            double py = cy + pileOffsets[pi].dy;

                            try
                            {
                                var dsPile = CreatePileDirectShape(doc, px, py, depth, concreteMaterial, gridName, pileK);
                                pilesCreated++;
                                Log($"Created DirectShape pile 'SUB-PILE-{gridName}-{pileK}' at ({px:F2},{py:F2}), depth -{depth:F2} to -{depth + 24.0:F2} m.");
                            }
                            catch (Exception exPile)
                            {
                                failureCount++;
                                Log($"ERROR creating pile {pileK} for cap {gridName} at ({px:F2},{py:F2}): {exPile.Message}");
                            }
                        }
                    }

                    tx.Commit();
                }
                Log($"Pile caps created: {capsCreated} / {designData.Caps.Count}");
                Log($"Piles created: {pilesCreated} / 70");

                // -------------------------------------------------------------
                // Phase 4: Create Grade Beams (300x600 along grid lines)
                // -------------------------------------------------------------
                if (symGradeBeam == null)
                {
                    Log("ERROR: Grade beam symbol 'GB 300x600' is not available. Cannot create grade beams.");
                    failureCount += 31;
                }
                else
                {
                    using (var tx = new Transaction(doc, "Generate Grade Beams"))
                    {
                        tx.Start();

                        double[] colXs = { 0.0, 5.0, 10.0, 15.0, 20.0 };
                        double[] colYs = { 0.0, 5.0, 10.0, 15.0 };
                        int gbIndex = 1;

                        // X-direction: 4 bays × 4 lines = 16
                        foreach (double y in colYs)
                        {
                            for (int bay = 0; bay < colXs.Length - 1; bay++)
                            {
                                double x1 = colXs[bay];
                                double x2 = colXs[bay + 1];

                                try
                                {
                                    var p1 = new XYZ(MToFt(x1), MToFt(y), baseLevel.Elevation);
                                    var p2 = new XYZ(MToFt(x2), MToFt(y), baseLevel.Elevation);
                                    var line = Line.CreateBound(p1, p2);
                                    var beam = doc.Create.NewFamilyInstance(line, symGradeBeam, baseLevel, StructuralType.Beam);

                                    // Ensure top of beam is at z = 0.0
                                    var zJust = beam.get_Parameter(BuiltInParameter.Z_JUSTIFICATION);
                                    if (zJust != null && !zJust.IsReadOnly && zJust.AsInteger() != 0)
                                    {
                                        zJust.Set(0); // Top
                                    }
                                    var zOffset = beam.get_Parameter(BuiltInParameter.Z_OFFSET_VALUE);
                                    if (zOffset != null && !zOffset.IsReadOnly)
                                    {
                                        zOffset.Set(0.0);
                                    }

                                    string mark = $"SUB-GB-{gbIndex++}";
                                    SetMarkAndComments(beam, mark, "SUB: grade/tie beam (BNBC seismic interconnection of pile caps)");
                                    gradeBeamsCreated++;
                                }
                                catch (Exception exGbX)
                                {
                                    failureCount++;
                                    Log($"ERROR creating X grade beam at y={y}, x={x1}->{x2}: {exGbX.Message}");
                                }
                            }
                        }

                        // Y-direction: 3 bays × 5 lines = 15
                        foreach (double x in colXs)
                        {
                            for (int bay = 0; bay < colYs.Length - 1; bay++)
                            {
                                double y1 = colYs[bay];
                                double y2 = colYs[bay + 1];

                                try
                                {
                                    var p1 = new XYZ(MToFt(x), MToFt(y1), baseLevel.Elevation);
                                    var p2 = new XYZ(MToFt(x), MToFt(y2), baseLevel.Elevation);
                                    var line = Line.CreateBound(p1, p2);
                                    var beam = doc.Create.NewFamilyInstance(line, symGradeBeam, baseLevel, StructuralType.Beam);

                                    var zJust = beam.get_Parameter(BuiltInParameter.Z_JUSTIFICATION);
                                    if (zJust != null && !zJust.IsReadOnly && zJust.AsInteger() != 0)
                                    {
                                        zJust.Set(0); // Top
                                    }
                                    var zOffset = beam.get_Parameter(BuiltInParameter.Z_OFFSET_VALUE);
                                    if (zOffset != null && !zOffset.IsReadOnly)
                                    {
                                        zOffset.Set(0.0);
                                    }

                                    string mark = $"SUB-GB-{gbIndex++}";
                                    SetMarkAndComments(beam, mark, "SUB: grade/tie beam (BNBC seismic interconnection of pile caps)");
                                    gradeBeamsCreated++;
                                }
                                catch (Exception exGbY)
                                {
                                    failureCount++;
                                    Log($"ERROR creating Y grade beam at x={x}, y={y1}->{y2}: {exGbY.Message}");
                                }
                            }
                        }

                        tx.Commit();
                    }
                }
                Log($"Grade beams created: {gradeBeamsCreated} / 31");

                // -------------------------------------------------------------
                // Phase 5: Setup Views (BIM 3D Foundations & BIM 3D)
                // -------------------------------------------------------------
                View3D? viewFoundations = null;
                View3D? viewBim3D = null;

                using (var tx = new Transaction(doc, "Setup Foundation 3D Views"))
                {
                    tx.Start();

                    // Locate or create "BIM 3D Foundations"
                    viewFoundations = new FilteredElementCollector(doc)
                        .OfClass(typeof(View3D))
                        .Cast<View3D>()
                        .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("BIM 3D Foundations", StringComparison.OrdinalIgnoreCase));

                    if (viewFoundations == null)
                    {
                        var vft3D = new FilteredElementCollector(doc)
                            .OfClass(typeof(ViewFamilyType))
                            .Cast<ViewFamilyType>()
                            .FirstOrDefault(v => v.ViewFamily == ViewFamily.ThreeDimensional);

                        if (vft3D == null)
                        {
                            throw new InvalidOperationException("ViewFamilyType for ThreeDimensional not found.");
                        }

                        viewFoundations = View3D.CreateIsometric(doc, vft3D.Id);
                        viewFoundations.Name = "BIM 3D Foundations";
                        Log("Created 3D Isometric View 'BIM 3D Foundations'.");
                    }
                    else
                    {
                        Log("Reusing existing 3D View 'BIM 3D Foundations'.");
                    }

                    viewFoundations.DetailLevel = ViewDetailLevel.Fine;
                    viewFoundations.DisplayStyle = DisplayStyle.Shading;

                    // Set section box to show whole building down to -26 m (and margin to -28 m)
                    var box = new BoundingBoxXYZ
                    {
                        Min = new XYZ(MToFt(-5.0), MToFt(-5.0), MToFt(-28.0)),
                        Max = new XYZ(MToFt(25.0), MToFt(20.0), MToFt(36.0))
                    };
                    viewFoundations.SetSectionBox(box);
                    viewFoundations.IsSectionBoxActive = true;
                    Log("Configured section box on 'BIM 3D Foundations' from z = -28 m to +36 m.");

                    // Also locate main view "BIM 3D"
                    viewBim3D = new FilteredElementCollector(doc)
                        .OfClass(typeof(View3D))
                        .Cast<View3D>()
                        .FirstOrDefault(v => !v.IsTemplate && v.Name.Equals("BIM 3D", StringComparison.OrdinalIgnoreCase));

                    if (viewBim3D != null && viewBim3D.IsSectionBoxActive)
                    {
                        var curBox = viewBim3D.GetSectionBox();
                        if (curBox.Min.Z > MToFt(-26.0))
                        {
                            curBox.Min = new XYZ(curBox.Min.X, curBox.Min.Y, MToFt(-28.0));
                            viewBim3D.SetSectionBox(curBox);
                            Log("Expanded section box on 'BIM 3D' to include piles down to -28 m.");
                        }
                    }

                    tx.Commit();
                }

                // -------------------------------------------------------------
                // Phase 6: Model Summary Logging
                // -------------------------------------------------------------
                Log("================================================================================");
                Log("SUBSTRUCTURE MODEL SUMMARY:");
                Log($"  Pile Caps:   {capsCreated} / {designData.Caps.Count}");
                Log($"  Piles:       {pilesCreated} / 70");
                Log($"  Grade Beams: {gradeBeamsCreated} / 31");
                Log($"  Total Added: {capsCreated + pilesCreated + gradeBeamsCreated} elements");
                Log($"  Failures:    {failureCount}");
                Log("================================================================================");

                // -------------------------------------------------------------
                // Phase 7: Save & Re-export IFC and PNGs
                // -------------------------------------------------------------
                Log($"Saving updated structural model to '{RvtPath}'...");
                try
                {
                    doc.Save();
                    Log("Saved with doc.Save().");
                }
                catch (Exception exSave)
                {
                    Log($"doc.Save() failed ({exSave.Message}). Attempting doc.SaveAs...");
                    doc.SaveAs(RvtPath, new SaveAsOptions { OverwriteExistingFile = true });
                    Log("Saved with doc.SaveAs().");
                }

                Log($"Re-exporting structural IFC to '{BimDir}\\{IfcFileName}'...");
                ExportIfc(doc, BimDir, IfcFileName);

                if (viewFoundations != null)
                {
                    Log($"Exporting Foundations 3D PNG to '{FoundationsPngPath}'...");
                    ExportPngView(doc, viewFoundations, FoundationsPngPath);
                }

                if (viewBim3D != null)
                {
                    Log($"Re-exporting main 3D PNG to '{PngPath}'...");
                    ExportPngView(doc, viewBim3D, PngPath);
                }

                if (doc.IsModified)
                {
                    doc.Save();
                }

                return failureCount == 0 && capsCreated == designData.Caps.Count && pilesCreated == 70 && gradeBeamsCreated == 31;
            }
            catch (Exception ex)
            {
                Log($"FATAL ERROR in ExecuteSubPipeline: {ex}");
                return false;
            }
            finally
            {
                if (doc != null)
                {
                    try
                    {
                        Log("Closing structural document...");
                        doc.Close(false);
                        Log("Structural document closed successfully.");
                    }
                    catch (Exception exClose)
                    {
                        Log($"Exception closing structural document: {exClose.Message}");
                    }
                }
            }
        }

        private static string FormatDimension(double val)
        {
            if (Math.Abs(val - Math.Round(val)) < 0.001)
            {
                return val.ToString("0.0", CultureInfo.InvariantCulture);
            }
            return val.ToString("0.##", CultureInfo.InvariantCulture);
        }

        private static string GetGridName(double x, double y)
        {
            string colLetter = Math.Abs(x - 0.0) < 0.1 ? "A" :
                               Math.Abs(x - 5.0) < 0.1 ? "B" :
                               Math.Abs(x - 10.0) < 0.1 ? "C" :
                               Math.Abs(x - 15.0) < 0.1 ? "D" :
                               Math.Abs(x - 20.0) < 0.1 ? "E" : $"X{x:F0}";

            string rowNumber = Math.Abs(y - 0.0) < 0.1 ? "1" :
                               Math.Abs(y - 5.0) < 0.1 ? "2" :
                               Math.Abs(y - 10.0) < 0.1 ? "3" :
                               Math.Abs(y - 15.0) < 0.1 ? "4" : $"Y{y:F0}";

            return $"{colLetter}{rowNumber}";
        }

        private static List<(double dx, double dy)> GetPileOffsets(int n)
        {
            var offsets = new List<(double dx, double dy)>();
            switch (n)
            {
                case 2:
                    offsets.Add((-0.9, 0.0));
                    offsets.Add((0.9, 0.0));
                    break;
                case 3:
                    offsets.Add((-0.9, -0.5196));
                    offsets.Add((0.9, -0.5196));
                    offsets.Add((0.0, 1.0392));
                    break;
                case 5:
                    offsets.Add((-0.9, -0.9));
                    offsets.Add((0.9, -0.9));
                    offsets.Add((-0.9, 0.9));
                    offsets.Add((0.9, 0.9));
                    offsets.Add((0.0, 0.0));
                    break;
                default:
                    Log($"WARNING: Unexpected pile count n={n}. Defaulting to center pile.");
                    offsets.Add((0.0, 0.0));
                    break;
            }
            return offsets;
        }

        private static bool TrySetFootingDimensions(
            FamilySymbol symbol,
            double widthFt,
            double lengthFt,
            double thicknessFt,
            ElementId materialId,
            out string loggedDetails)
        {
            var details = new List<string>();

            // Width
            bool widthSet = false;
            string[] widthNames = { "Width", "width", "Width (b)", "b", "B" };
            foreach (var name in widthNames)
            {
                var p = symbol.LookupParameter(name);
                if (p != null && !p.IsReadOnly && p.StorageType == StorageType.Double)
                {
                    p.Set(widthFt);
                    widthSet = true;
                    details.Add($"width via '{name}' ({widthFt:F4} ft)");
                    break;
                }
            }
            if (!widthSet)
            {
                var bip = symbol.get_Parameter(BuiltInParameter.FAMILY_WIDTH_PARAM);
                if (bip != null && !bip.IsReadOnly)
                {
                    bip.Set(widthFt);
                    widthSet = true;
                    details.Add($"width via BuiltInParameter.FAMILY_WIDTH_PARAM ({widthFt:F4} ft)");
                }
            }

            // Length
            bool lengthSet = false;
            string[] lengthNames = { "Length", "length", "Length (l)", "l", "L" };
            foreach (var name in lengthNames)
            {
                var p = symbol.LookupParameter(name);
                if (p != null && !p.IsReadOnly && p.StorageType == StorageType.Double)
                {
                    p.Set(lengthFt);
                    lengthSet = true;
                    details.Add($"length via '{name}' ({lengthFt:F4} ft)");
                    break;
                }
            }

            // Thickness
            bool thicknessSet = false;
            string[] thickNames = { "Foundation Thickness", "Foundation thickness", "Thickness", "thickness", "Thickness (h)", "h", "Height", "depth", "Depth" };
            foreach (var name in thickNames)
            {
                var p = symbol.LookupParameter(name);
                if (p != null && !p.IsReadOnly && p.StorageType == StorageType.Double)
                {
                    p.Set(thicknessFt);
                    thicknessSet = true;
                    details.Add($"thickness via '{name}' ({thicknessFt:F4} ft)");
                    break;
                }
            }
            if (!thicknessSet)
            {
                var bip = symbol.get_Parameter(BuiltInParameter.STRUCTURAL_FOUNDATION_THICKNESS);
                if (bip != null && !bip.IsReadOnly)
                {
                    bip.Set(thicknessFt);
                    thicknessSet = true;
                    details.Add($"thickness via BuiltInParameter.STRUCTURAL_FOUNDATION_THICKNESS ({thicknessFt:F4} ft)");
                }
            }

            // Material
            if (materialId != ElementId.InvalidElementId)
            {
                string[] matNames = { "Structural Material", "Material", "Foundation Material" };
                foreach (var name in matNames)
                {
                    var p = symbol.LookupParameter(name);
                    if (p != null && !p.IsReadOnly && p.StorageType == StorageType.ElementId)
                    {
                        p.Set(materialId);
                        details.Add($"material via '{name}'");
                        break;
                    }
                }
            }

            loggedDetails = string.Join(", ", details);
            return widthSet && lengthSet && thicknessSet;
        }

        private static DirectShape CreatePileCapDirectShape(
            Document doc,
            double cx,
            double cy,
            double lx,
            double ly,
            double depth,
            Material? material,
            string gridName,
            int nPiles)
        {
            double zBottom = MToFt(-depth);
            double hFt = MToFt(depth);
            double halfLx = MToFt(lx / 2.0);
            double halfLy = MToFt(ly / 2.0);
            double cxFt = MToFt(cx);
            double cyFt = MToFt(cy);

            var p1 = new XYZ(cxFt - halfLx, cyFt - halfLy, zBottom);
            var p2 = new XYZ(cxFt + halfLx, cyFt - halfLy, zBottom);
            var p3 = new XYZ(cxFt + halfLx, cyFt + halfLy, zBottom);
            var p4 = new XYZ(cxFt - halfLx, cyFt + halfLy, zBottom);

            var loop = new CurveLoop();
            loop.Append(Line.CreateBound(p1, p2));
            loop.Append(Line.CreateBound(p2, p3));
            loop.Append(Line.CreateBound(p3, p4));
            loop.Append(Line.CreateBound(p4, p1));

            Solid capSolid = GeometryCreationUtilities.CreateExtrusionGeometry(
                new List<CurveLoop> { loop },
                XYZ.BasisZ,
                hFt);

            var ds = DirectShape.CreateElement(doc, new ElementId(BuiltInCategory.OST_StructuralFoundation));
            ds.ApplicationId = "PrefabBIM";
            ds.ApplicationDataId = Guid.NewGuid().ToString();
            ds.SetShape(new List<GeometryObject> { capSolid });

            if (material != null)
            {
                AssignMaterialToDirectShape(doc, ds, material.Id, "Concrete Pile Cap Type");
            }

            string mark = $"SUB-CAP-{gridName}";
            string comments = $"SUB: pile cap, {nPiles} piles";
            SetMarkAndComments(ds, mark, comments);

            return ds;
        }

        private static DirectShape CreatePileDirectShape(
            Document doc,
            double px,
            double py,
            double capDepth,
            Material? material,
            string gridName,
            int pileIndex)
        {
            double rFt = MToFt(0.3);
            double lenFt = MToFt(24.0);
            double zToeFt = MToFt(-capDepth - 24.0);
            double pxFt = MToFt(px);
            double pyFt = MToFt(py);

            var p1 = new XYZ(pxFt + rFt, pyFt, zToeFt);
            var p2 = new XYZ(pxFt - rFt, pyFt, zToeFt);
            var mid1 = new XYZ(pxFt, pyFt + rFt, zToeFt);
            var mid2 = new XYZ(pxFt, pyFt - rFt, zToeFt);

            var arc1 = Arc.Create(p1, p2, mid1);
            var arc2 = Arc.Create(p2, p1, mid2);

            var loop = new CurveLoop();
            loop.Append(arc1);
            loop.Append(arc2);

            Solid pileSolid = GeometryCreationUtilities.CreateExtrusionGeometry(
                new List<CurveLoop> { loop },
                XYZ.BasisZ,
                lenFt);

            var ds = DirectShape.CreateElement(doc, new ElementId(BuiltInCategory.OST_StructuralFoundation));
            ds.ApplicationId = "PrefabBIM";
            ds.ApplicationDataId = Guid.NewGuid().ToString();
            ds.SetShape(new List<GeometryObject> { pileSolid });

            if (material != null)
            {
                AssignMaterialToDirectShape(doc, ds, material.Id, "Concrete Pile Type");
            }

            string mark = $"SUB-PILE-{gridName}-{pileIndex}";
            string comments = "SUB: bored pile 600 mm x 24 m (cast-in-situ)";
            SetMarkAndComments(ds, mark, comments);

            return ds;
        }

        private static void AssignMaterialToDirectShape(Document doc, DirectShape ds, ElementId matId, string typeName)
        {
            if (matId == ElementId.InvalidElementId) return;

            try
            {
                // 1. Try instance parameter
                var matParam = ds.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)
                               ?? ds.LookupParameter("Material")
                               ?? ds.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM);
                if (matParam != null && !matParam.IsReadOnly)
                {
                    matParam.Set(matId);
                    Log($"DirectShape Id {ds.Id}: Assigned material directly via instance parameter.");
                    return;
                }

                // 2. Try DirectShapeType if supported
                try
                {
                    var dsType = new FilteredElementCollector(doc)
                        .OfClass(typeof(DirectShapeType))
                        .Cast<DirectShapeType>()
                        .FirstOrDefault(t => t.Name == typeName);

                    if (dsType == null)
                    {
                        dsType = DirectShapeType.Create(doc, typeName, new ElementId(BuiltInCategory.OST_StructuralFoundation));
                        var typeMatParam = dsType.get_Parameter(BuiltInParameter.MATERIAL_ID_PARAM)
                                           ?? dsType.LookupParameter("Material")
                                           ?? dsType.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM);
                        if (typeMatParam != null && !typeMatParam.IsReadOnly)
                        {
                            typeMatParam.Set(matId);
                        }
                    }

                    if (dsType != null)
                    {
                        ds.ChangeTypeId(dsType.Id);
                        Log($"DirectShape Id {ds.Id}: Assigned material via DirectShapeType '{typeName}'.");
                        return;
                    }
                }
                catch (Exception exType)
                {
                    Log($"DirectShape Id {ds.Id}: DirectShapeType material assignment skipped ({exType.Message}).");
                }

                Log($"DirectShape Id {ds.Id}: Material parameter not directly settable on instance or type, skipped material.");
            }
            catch (Exception ex)
            {
                Log($"DirectShape Id {ds.Id}: Material assignment exception ({ex.Message}), skipped material.");
            }
        }

        // =========================================================================
        // Substructure Data Transfer Objects
        // =========================================================================
        public class PileDesignData
        {
            [JsonPropertyName("Qa")]
            public double Qa { get; set; }

            [JsonPropertyName("Qt")]
            public double Qt { get; set; }

            [JsonPropertyName("H_allow")]
            public double HAllow { get; set; }

            [JsonPropertyName("total_piles")]
            public int TotalPiles { get; set; }

            [JsonPropertyName("caps")]
            public List<PileCapData> Caps { get; set; } = new List<PileCapData>();
        }

        public class PileCapData
        {
            [JsonPropertyName("n")]
            public int N { get; set; }

            [JsonPropertyName("cap_LxLyT")]
            public List<double> CapLxLyT { get; set; } = new List<double>();

            [JsonPropertyName("xy")]
            public List<double> Xy { get; set; } = new List<double>();

            [JsonPropertyName("joint")]
            public string? Joint { get; set; }

            [JsonIgnore]
            public double X => Xy.Count > 0 ? Xy[0] : 0.0;

            [JsonIgnore]
            public double Y => Xy.Count > 1 ? Xy[1] : 0.0;

            [JsonIgnore]
            public double Lx => CapLxLyT.Count > 0 ? CapLxLyT[0] : 0.0;

            [JsonIgnore]
            public double Ly => CapLxLyT.Count > 1 ? CapLxLyT[1] : 0.0;

            [JsonIgnore]
            public double Depth => CapLxLyT.Count > 2 ? CapLxLyT[2] : 0.0;
        }

        private static bool IsWallEndColumn(double x, double y)
        {
            const double tol = 0.01;
            return (Math.Abs(x - 0.0) < tol && (Math.Abs(y - 5.0) < tol || Math.Abs(y - 10.0) < tol))
                || (Math.Abs(x - 20.0) < tol && (Math.Abs(y - 5.0) < tol || Math.Abs(y - 10.0) < tol))
                || ((Math.Abs(x - 5.0) < tol || Math.Abs(x - 10.0) < tol) && Math.Abs(y - 0.0) < tol)
                || ((Math.Abs(x - 10.0) < tol || Math.Abs(x - 15.0) < tol) && Math.Abs(y - 15.0) < tol);
        }

        private static FamilySymbol GetOrCreateFamilySymbol(FamilySymbol baseSymbol, string typeName)
        {
            var family = baseSymbol.Family;
            foreach (ElementId symId in family.GetFamilySymbolIds())
            {
                if (baseSymbol.Document.GetElement(symId) is FamilySymbol fs && fs.Name.Equals(typeName, StringComparison.OrdinalIgnoreCase))
                {
                    if (!fs.IsActive) fs.Activate();
                    return fs;
                }
            }

            var newSym = baseSymbol.Duplicate(typeName) as FamilySymbol;
            if (newSym == null)
            {
                throw new InvalidOperationException($"Failed to duplicate symbol to '{typeName}'");
            }
            if (!newSym.IsActive)
            {
                newSym.Activate();
            }
            return newSym;
        }

        private static void SetDimensionParameters(FamilySymbol symbol, double widthFt, double heightFt, ElementId materialId, string typeLabel)
        {
            // Width / b parameter
            bool widthSet = false;
            string[] widthNames = { "b", "B", "Width", "width", "Width (b)", "b (Width)" };
            foreach (var name in widthNames)
            {
                var p = symbol.LookupParameter(name);
                if (p != null && !p.IsReadOnly && p.StorageType == StorageType.Double)
                {
                    p.Set(widthFt);
                    widthSet = true;
                    Log($"Symbol '{typeLabel}': Set width parameter '{name}' = {widthFt:F4} ft");
                    break;
                }
            }
            if (!widthSet)
            {
                var bip = symbol.get_Parameter(BuiltInParameter.FAMILY_WIDTH_PARAM);
                if (bip != null && !bip.IsReadOnly)
                {
                    bip.Set(widthFt);
                    widthSet = true;
                    Log($"Symbol '{typeLabel}': Set BuiltInParameter.FAMILY_WIDTH_PARAM = {widthFt:F4} ft");
                }
            }

            // Height / Depth / h parameter
            bool heightSet = false;
            string[] heightNames = { "h", "H", "Depth", "depth", "Height", "height", "Height (h)", "Depth (h)", "h (Height)" };
            foreach (var name in heightNames)
            {
                var p = symbol.LookupParameter(name);
                if (p != null && !p.IsReadOnly && p.StorageType == StorageType.Double)
                {
                    p.Set(heightFt);
                    heightSet = true;
                    Log($"Symbol '{typeLabel}': Set depth/height parameter '{name}' = {heightFt:F4} ft");
                    break;
                }
            }
            if (!heightSet)
            {
                var bip = symbol.get_Parameter(BuiltInParameter.FAMILY_HEIGHT_PARAM);
                if (bip != null && !bip.IsReadOnly)
                {
                    bip.Set(heightFt);
                    heightSet = true;
                    Log($"Symbol '{typeLabel}': Set BuiltInParameter.FAMILY_HEIGHT_PARAM = {heightFt:F4} ft");
                }
            }

            if (!widthSet || !heightSet)
            {
                var availableParams = string.Join(", ", symbol.Parameters.Cast<Parameter>().Select(p => p.Definition.Name));
                Log($"WARNING: Could not set full dimensions on '{typeLabel}'. Available parameters: {availableParams}");
            }

            // Material parameter
            if (materialId != ElementId.InvalidElementId)
            {
                bool matSet = false;
                string[] matNames = { "Structural Material", "Material", "Column Material", "Structural Material (Concrete)" };
                foreach (var name in matNames)
                {
                    var p = symbol.LookupParameter(name);
                    if (p != null && !p.IsReadOnly && p.StorageType == StorageType.ElementId)
                    {
                        p.Set(materialId);
                        matSet = true;
                        Log($"Symbol '{typeLabel}': Set material parameter '{name}'");
                        break;
                    }
                }
                if (!matSet)
                {
                    var bip = symbol.get_Parameter(BuiltInParameter.STRUCTURAL_MATERIAL_PARAM);
                    if (bip != null && !bip.IsReadOnly)
                    {
                        bip.Set(materialId);
                        Log($"Symbol '{typeLabel}': Set BuiltInParameter.STRUCTURAL_MATERIAL_PARAM");
                    }
                }
            }
        }

        private static void SetMarkAndComments(Element elem, string mark, string? comments = null)
        {
            var markParam = elem.get_Parameter(BuiltInParameter.ALL_MODEL_MARK) ?? elem.LookupParameter("Mark");
            if (markParam != null && !markParam.IsReadOnly)
            {
                markParam.Set(mark);
            }

            if (!string.IsNullOrEmpty(comments))
            {
                var commentParam = elem.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS) ?? elem.LookupParameter("Comments");
                if (commentParam != null && !commentParam.IsReadOnly)
                {
                    commentParam.Set(comments);
                }
            }
        }

        private static void ExportIfc(Document doc, string folder, string fileName)
        {
            try
            {
                var options = new IFCExportOptions { FileVersion = IFCVersion.IFC4RV };
                doc.Export(folder, fileName, options);
                Log($"IFC export succeeded with IFC4RV at '{Path.Combine(folder, fileName)}'");
            }
            catch (Exception ex1)
            {
                Log($"Direct IFC export (IFC4RV) returned: {ex1.Message}. Retrying within Transaction...");
                try
                {
                    using (var tx = new Transaction(doc, "Export IFC"))
                    {
                        tx.Start();
                        var options = new IFCExportOptions { FileVersion = IFCVersion.IFC4RV };
                        doc.Export(folder, fileName, options);
                        tx.Commit();
                        Log("IFC export succeeded within transaction.");
                    }
                }
                catch (Exception ex2)
                {
                    Log($"IFC4RV in transaction failed: {ex2.Message}. Retrying with IFC2x3CV2...");
                    try
                    {
                        using (var tx = new Transaction(doc, "Export IFC fallback"))
                        {
                            tx.Start();
                            var options = new IFCExportOptions { FileVersion = IFCVersion.IFC2x3CV2 };
                            doc.Export(folder, fileName, options);
                            tx.Commit();
                            Log("IFC export succeeded with IFC2x3CV2.");
                        }
                    }
                    catch (Exception ex3)
                    {
                        Log($"ERROR: All IFC export attempts failed: {ex3}");
                    }
                }
            }
        }

        private static void ExportPngView(Document doc, View3D view, string targetPngPath)
        {
            try
            {
                string targetDir = Path.GetDirectoryName(targetPngPath) ?? BimDir;
                string baseNameWithoutExt = Path.GetFileNameWithoutExtension(targetPngPath);
                string tempPrefix = Path.Combine(targetDir, baseNameWithoutExt);

                var imgOptions = new ImageExportOptions
                {
                    ZoomType = ZoomFitType.FitToPage,
                    PixelSize = 1600,
                    FilePath = tempPrefix,
                    FitDirection = FitDirectionType.Horizontal,
                    HLRandWFViewsFileType = ImageFileType.PNG,
                    ShadowViewsFileType = ImageFileType.PNG,
                    ImageResolution = ImageResolution.DPI_150,
                    ExportRange = ExportRange.SetOfViews
                };
                imgOptions.SetViewsAndSheets(new List<ElementId> { view.Id });

                doc.ExportImage(imgOptions);
                Log("ExportImage command executed.");

                // Look for files matching baseName that Revit generated with view names appended
                var matching = Directory.GetFiles(targetDir, $"{baseNameWithoutExt}*.png")
                    .Where(f => !string.Equals(f, targetPngPath, StringComparison.OrdinalIgnoreCase))
                    .OrderByDescending(f => File.GetLastWriteTimeUtc(f))
                    .ToList();

                if (matching.Count > 0)
                {
                    var createdFile = matching.First();
                    File.Copy(createdFile, targetPngPath, true);
                    Log($"Copied generated image '{createdFile}' to target path '{targetPngPath}'");
                }
                else if (File.Exists(targetPngPath))
                {
                    Log($"Target PNG file exists at expected path: '{targetPngPath}'");
                }
                else
                {
                    Log($"WARNING: No matching PNG output found starting with '{baseNameWithoutExt}'");
                }
            }
            catch (Exception ex)
            {
                Log($"ERROR exporting 3D PNG view: {ex}");
            }
        }

        private static double MToFt(double meters) => UnitUtils.ConvertToInternalUnits(meters, UnitTypeId.Meters);
        private static double MmToFt(double mm) => UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters);

        public static void Log(string message)
        {
            try
            {
                lock (_logLock)
                {
                    var line = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff}] {message}";
                    File.AppendAllText(_currentLogPath, line + Environment.NewLine);
                }
            }
            catch
            {
                // Suppress file I/O exceptions in logger
            }
        }
    }
}
