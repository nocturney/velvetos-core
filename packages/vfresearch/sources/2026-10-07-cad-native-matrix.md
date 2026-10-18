# CAD native technology matrix — 2026-10-07

This is a research matrix only. It does not modify the active AI 3D/CAD Core branch or select a new canonical engine.

| Technology | Primary representation / strength | Candidate VelvetOS role | Decision now |
|---|---|---|---|
| OpenCASCADE | B-Rep / STEP / solid modeling | exact CAD kernel, STEP healing and exchange | compare against current build123d/FreeCAD path after AI3D checkpoint |
| CGAL | computational geometry | robust mesh/solid algorithms, intersections, remeshing | targeted library candidate |
| libigl | mesh geometry processing | lightweight mesh analysis/repair research | targeted library candidate |
| Open3D | point clouds / meshes / reconstruction | scan and reconstruction workflows | targeted library candidate |
| OpenVDB | sparse volumes / level sets | voxel/SDF/volume conversion | later specialized provider |
| Assimp | asset interchange | broad mesh scene import/export | utility candidate, not CAD kernel |
| Eigen | linear algebra | native numerical dependency | dependency, not provider |
| Ceres Solver | nonlinear optimization | fitting/calibration/reconstruction | later specialized dependency |
| PCL | point clouds | scan processing and registration | compare with Open3D before adoption |
| MeshLib | mesh/point-cloud processing | repair, inspection and geometry operations | audit against license/API/current stack |

## Gate

Runtime choices wait for the active AI 3D Engineering Core to reach a stable checkpoint or merge. No library in this matrix gains printer control or fabrication authority.
