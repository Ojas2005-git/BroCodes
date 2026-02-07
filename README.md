# BroCodes
**HackArena 3.0 - Advanced River Labeling System**

A sophisticated web-based map visualization tool that renders WKT (Well-Known Text) geometries with intelligent, curved text labels that follow river centerlines.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone or download the repository**
   ```bash
   cd BroCodes
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   - **Windows:**
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open in browser**
   - Navigate to `http://127.0.0.1:5000/`
   - Use the controls to zoom in/out, toggle labels, and show debug points

---

## 📋 Project Requirements & Implementation

This project implements an advanced river labeling system that satisfies **5 critical requirements**:

### ✅ Requirement 1: Text Must Be Fully Inside the River

**Implementation:**
- **Distance Field Spine Algorithm** (`getDistanceFieldSpine()` function)
  - Samples a grid of points inside the polygon
  - For each point, calculates the minimum distance to all polygon edges
  - Identifies the point with maximum distance from edges (the "centerline")
  - Traces a spine along the river by following the ridge of maximum distances
  
- **Padding Enforcement** (`placeLabels()` function, lines 620-622)
  ```javascript
  const maxW = Math.max(...spine.map(s => s.width));
  const allInside = maxW > (fontSize + padding * 2);
  ```
  - Checks if the widest part of the spine can accommodate text + padding
  - Only places labels inside if there's sufficient clearance from edges
  - `padding = fontSize * 0.5` ensures text never touches river boundaries

### ✅ Requirement 2: Optimal Readability

**Implementation:**
- **Centerline Placement** (`getDistanceFieldSpine()` function, lines 466-568)
  - Labels are placed along the computed spine (geometric centerline)
  - The spine follows the widest/most visible parts of the river
  - Avoids narrow bends by selecting points with maximum edge distance

- **Centered & Visible Positioning** (`placeLabels()` function, lines 630-640)
  ```javascript
  const f = (i + 0.5) / count;  // Center each label in its segment
  const targetDist = totalLength * f;
  ```
  - Distributes labels evenly along the spine length
  - Each label is centered within its allocated segment
  - Filters out polygons with area < 500 pixels (too small for readable text)

- **Zoom-Adaptive Density** (lines 626-628)
  ```javascript
  const densityFactor = 2.0 * zoomScale;
  const count = Math.min(3, Math.max(1, Math.floor(totalLength / (labelWidth * densityFactor))));
  ```
  - Adjusts number of labels based on zoom level
  - Prevents overcrowding at high zoom levels
  - Maximum 3 labels per river polygon

### ✅ Requirement 3: Fallback Rule - Outside Placement

**Implementation:**
- **Inside/Outside Decision Logic** (lines 620-658)
  ```javascript
  if (allInside) {
    drawCurvedLabel(ctx, riverName, spine, lengths, targetDist, fontSize, COLORS.labelInside, 0);
  } else if (i === 0) {
    const offsetDist = (nav.width / 2) + fontSize * 0.8;
    drawCurvedLabel(ctx, riverName, spine, lengths, targetDist, fontSize * 0.9, COLORS.labelOutside, offsetDist);
  }
  ```
  
- **Fallback Behavior:**
  - If `maxW > (fontSize + padding * 2)`: Place all labels **inside** with white color
  - If insufficient width: Place **one label outside** with dark color
  - Outside labels are offset by `(riverWidth / 2) + fontSize * 0.8` to clear the river boundary
  - Uses different colors: white for inside, dark for outside (better contrast)

### ✅ Requirement 4: Rotate Text to Match River Flow Direction

**Implementation:**
- **Segment-Based Rotation** (`drawCurvedLabel()` function, lines 808-810)
  ```javascript
  const sample = getSpinePoint(spine, lengths, charDist);
  let angle = sample.angle;
  if (isReversed) angle += Math.PI;
  ```

- **Flow Direction Calculation** (`getSpinePoint()` function, lines 683)
  ```javascript
  const angle = Math.atan2(p1[1] - p0[1], p1[0] - p0[0]);
  ```
  - Calculates angle from spine segment direction (delta between consecutive points)
  - Each character is rotated to align with the local flow direction

- **Readability Flip** (lines 708-714)
  ```javascript
  let normAngle = baseAngle % (Math.PI * 2);
  if (normAngle > Math.PI) normAngle -= Math.PI * 2;
  const isReversed = (Math.abs(normAngle) > Math.PI / 2);
  ```
  - Automatically flips text 180° if it would appear upside-down
  - Ensures text is always readable (right-side-up)
  - Reverses character order when flipped to maintain correct reading direction

### ✅ Requirement 5: Curve Text Along River Centerline

**Implementation:**
- **Character-by-Character Rendering** (`drawCurvedLabel()` function, lines 738-823)
  ```javascript
  chars.forEach(char => {
    const charW = ctx.measureText(char).width;
    const charDist = centerDist + currentDistOffset + charW / 2;
    const sample = getSpinePoint(spine, lengths, charDist);
    
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle);
    ctx.fillText(char, 0, 0);
    ctx.restore();
  });
  ```

- **Curved Path Following:**
  - Text is split into individual characters
  - Each character is positioned at a specific distance along the spine
  - `getSpinePoint()` interpolates position and angle along the curved spine
  - Characters are individually rotated and translated to follow the curve

- **Perpendicular Offset for Outside Labels** (lines 812-816)
  ```javascript
  const nx = -Math.sin(angle);
  const ny = Math.cos(angle);
  const x = sample.pt[0] + nx * renderOffset;
  const y = sample.pt[1] + ny * renderOffset;
  ```
  - Calculates perpendicular normal vector to the spine
  - Offsets characters perpendicular to flow direction
  - Maintains consistent distance from centerline for outside labels

---

## 🏗️ Architecture Overview

### Backend (`app.py`)
- **Flask web server** serving the visualization
- **WKT parsing** using Shapely library
- **Geometry normalization** to canvas coordinates
- **Data pipeline:**
  1. Load WKT from `data.wkt`
  2. Extract polygons and lines
  3. Normalize to [-0.5, 0.5] range
  4. Scale to canvas pixels (600x600)
  5. Render Jinja2 template with data

### Frontend (`templates/index.html`)
- **HTML5 Canvas** for rendering
- **Interactive controls:** zoom, pan, toggle labels/points
- **Advanced geometry algorithms:**
  - Distance field computation
  - Spine extraction (centerline detection)
  - Curved text rendering
  - Rotation and readability optimization

### Key Algorithms

#### 1. Distance Field Spine Extraction
- Samples a 25x25 grid inside each polygon
- Finds the point farthest from all edges (maximum inscribed circle center)
- Traces outward in both directions along the ridge of maximum distances
- Creates a smooth spine representing the river centerline

#### 2. Curved Label Rendering
- Calculates cumulative arc length along spine
- Distributes characters evenly along the curve
- Interpolates position and rotation for each character
- Applies readability corrections (flip upside-down text)

#### 3. Inside/Outside Decision
- Compares maximum spine width to text bounding box + padding
- Places inside if sufficient clearance exists
- Falls back to outside placement with perpendicular offset

---

## 🎮 Interactive Features

- **Zoom In/Out:** Scale the map view
- **Pan:** Click and drag to move around
- **Toggle Labels:** Show/hide river labels
- **Show Points:** Display debug visualization of polygon vertices and spine points

---

## 📁 Project Structure

```
BroCodes/
├── app.py                 # Flask backend server
├── requirements.txt       # Python dependencies
├── data.wkt              # WKT geometry data (river polygons/lines)
├── labels.json           # Label configuration (river name)
└── templates/
    └── index.html        # Frontend visualization with Canvas rendering
```

---

## 🔧 Technical Stack

- **Backend:** Python 3.8+, Flask 3.0, Shapely 2.0
- **Frontend:** HTML5 Canvas, Vanilla JavaScript
- **Styling:** CSS3 with glassmorphism effects
- **Fonts:** Google Fonts (Inter)

---

## 📊 Algorithm Complexity

| Operation | Complexity | Description |
|-----------|-----------|-------------|
| Distance Field Computation | O(N × M × P) | N=grid density, M=polygon vertices, P=polygons |
| Spine Tracing | O(S × M) | S=spine steps, M=polygon vertices |
| Label Rendering | O(L × C) | L=labels, C=characters per label |
| Overall Per Frame | O(N × M × P) | Dominated by distance field computation |

**Optimizations:**
- Viewport buffering (150px) to reduce recomputation
- Area filtering (skip polygons < 500px²)
- Limit to top 5 largest polygons
- Smooth zoom animation with requestAnimationFrame

---

## 🎯 Future Enhancements

- [ ] Multi-river support with different label names
- [ ] Label collision detection and avoidance
- [ ] Export to SVG/PNG
- [ ] Custom color schemes
- [ ] Real-time WKT editing

---

## 📝 License

This project was created for HackArena 3.0.
