using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.DB.Events;
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
        private static readonly string BimDir = @"C:\Users\rashe\Documents\prefab\repo\BIM";
        private static readonly string LogFilePath = Path.Combine(BimDir, "build_log.txt");
        private static readonly string TemplatePath = @"C:\ProgramData\Autodesk\RVT 2027\Templates\English\Structural Analysis-DefaultMetric.rte";
        private static readonly string RvtPath = Path.Combine(BimDir, "Prefab_RCC_10storey.rvt");
        private static readonly string IfcFileName = "Prefab_RCC_10storey.ifc";
        private static readonly string PngPath = Path.Combine(BimDir, "Prefab_RCC_10storey_3D.png");

        public Result OnStartup(UIControlledApplication application)
        {
            _uiControlledApp = application;

            var jobEnv = Environment.GetEnvironmentVariable("PREFAB_BIM_JOB");
            if (jobEnv != "1")
            {
                // Standby mode: do nothing
                return Result.Succeeded;
            }

            Log("================================================================================");
            Log("PrefabBIM Add-in started. PREFAB_BIM_JOB=1 detected. Initializing job pipeline...");
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
            Log("PrefabBIM Add-in shutting down.");
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
            Log("ApplicationInitialized event fired. Beginning headless BIM construction...");

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
                buildSuccess = ExecuteBimGeneration(app);
            }
            catch (Exception ex)
            {
                Log($"FATAL UNHANDLED EXCEPTION in ExecuteBimGeneration: {ex}");
            }

            Log($"BIM Generation finished with result: {(buildSuccess ? "SUCCESS" : "FAILED")}. Registering Idling event for Revit exit...");

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

        private static bool ExecuteBimGeneration(Autodesk.Revit.ApplicationServices.Application app)
        {
            if (!File.Exists(TemplatePath))
            {
                Log($"ERROR: Template file does not exist at '{TemplatePath}'");
                return false;
            }

            if (!Directory.Exists(BimDir))
            {
                Directory.CreateDirectory(BimDir);
            }

            Log($"Opening template project: {TemplatePath}");
            Document doc = app.NewProjectDocument(TemplatePath);
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
                    // Reuse the template floor's compound structure (keeps floor-valid EndCap settings) and replace its layers.
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

                    // Grid layout definition
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

                                    // Set levels and offsets
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
                    // WY1: x=0, y: 5->10
                    // WY2: x=20, y: 5->10
                    // WX1: y=0, x: 5->10
                    // WX2: y=15, x: 10->15
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
                                    true); // Structural = true

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

                    // Floor Plans for all levels
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

                    // 3D Isometric View: "BIM 3D"
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

                // Re-save if IFC export or view export marked document as modified
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

        private static bool IsWallEndColumn(double x, double y)
        {
            // 8 wall-end positions: (0,5), (0,10), (20,5), (20,10), (5,0), (10,0), (10,15), (15,15)
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

        private static void SetMarkAndComments(Element elem, string mark, string comments)
        {
            var markParam = elem.get_Parameter(BuiltInParameter.ALL_MODEL_MARK) ?? elem.LookupParameter("Mark");
            if (markParam != null && !markParam.IsReadOnly)
            {
                markParam.Set(mark);
            }

            var commentParam = elem.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS) ?? elem.LookupParameter("Comments");
            if (commentParam != null && !commentParam.IsReadOnly)
            {
                commentParam.Set(comments);
            }
        }

        private static void ExportIfc(Document doc, string folder, string fileName)
        {
            try
            {
                // Attempt direct export
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

                // Revit often appends the view name, e.g. "Prefab_RCC_10storey_3D-3D View-BIM 3D.png"
                if (File.Exists(targetPngPath))
                {
                    Log($"Target PNG file exists at expected path: '{targetPngPath}'");
                }
                else
                {
                    // Search for generated matching files
                    var matching = Directory.GetFiles(targetDir, $"{baseNameWithoutExt}*.png");
                    if (matching.Length > 0)
                    {
                        var createdFile = matching.OrderByDescending(f => File.GetLastWriteTime(f)).First();
                        if (createdFile != targetPngPath)
                        {
                            File.Copy(createdFile, targetPngPath, true);
                            Log($"Copied generated image '{createdFile}' to target path '{targetPngPath}'");
                        }
                    }
                    else
                    {
                        Log($"WARNING: No matching PNG output found starting with '{baseNameWithoutExt}'");
                    }
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
                    File.AppendAllText(LogFilePath, line + Environment.NewLine);
                }
            }
            catch
            {
                // Suppress file I/O exceptions in logger
            }
        }
    }
}
