/* ============================================================
   cadview.js — dependency-free WebGL viewer for a binary glTF (.glb)
   Drag to orbit · scroll to zoom · right-drag / two-finger to pan
   ============================================================ */
(function () {
  'use strict';

  /* ------------------------------------------------------------- mat4 */
  function ident() { return new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]); }

  function perspective(fovy, aspect, near, far) {
    var f = 1 / Math.tan(fovy / 2), nf = 1 / (near - far);
    return new Float32Array([
      f / aspect, 0, 0, 0,
      0, f, 0, 0,
      0, 0, (far + near) * nf, -1,
      0, 0, 2 * far * near * nf, 0
    ]);
  }

  function lookAt(eye, center, up) {
    var z0 = eye[0]-center[0], z1 = eye[1]-center[1], z2 = eye[2]-center[2];
    var l = Math.hypot(z0, z1, z2) || 1; z0/=l; z1/=l; z2/=l;
    var x0 = up[1]*z2 - up[2]*z1, x1 = up[2]*z0 - up[0]*z2, x2 = up[0]*z1 - up[1]*z0;
    l = Math.hypot(x0, x1, x2);
    if (!l) { x0 = 1; x1 = 0; x2 = 0; } else { x0/=l; x1/=l; x2/=l; }
    var y0 = z1*x2 - z2*x1, y1 = z2*x0 - z0*x2, y2 = z0*x1 - z1*x0;
    return new Float32Array([
      x0, y0, z0, 0,
      x1, y1, z1, 0,
      x2, y2, z2, 0,
      -(x0*eye[0] + x1*eye[1] + x2*eye[2]),
      -(y0*eye[0] + y1*eye[1] + y2*eye[2]),
      -(z0*eye[0] + z1*eye[1] + z2*eye[2]), 1
    ]);
  }

  /* ------------------------------------------------------------- glb */
  function parseGLB(buf) {
    var dv = new DataView(buf);
    if (dv.getUint32(0, true) !== 0x46546C67) throw new Error('not a glb');
    var total = dv.getUint32(8, true);
    var off = 12, json = null, bin = null;
    while (off + 8 <= Math.min(total, dv.byteLength)) {
      var clen = dv.getUint32(off, true), ctype = dv.getUint32(off + 4, true);
      off += 8;
      if (ctype === 0x4E4F534A) {
        json = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, off, clen)));
      } else if (ctype === 0x004E4942) {
        bin = new Uint8Array(buf, off, clen);
      }
      off += clen;                     // chunk lengths are already 4-byte aligned
    }
    if (!json) throw new Error('no json chunk');
    return { json: json, bin: bin };
  }

  function accessorArray(g, bin, i) {
    var a = g.accessors[i], bv = g.bufferViews[a.bufferView];
    var off = (bv.byteOffset || 0) + (a.byteOffset || 0) + bin.byteOffset;
    var n = a.count * ({ SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 }[a.type]);
    switch (a.componentType) {
      case 5126: return new Float32Array(bin.buffer, off, n);
      case 5123: return new Uint16Array(bin.buffer, off, n);
      case 5125: return new Uint32Array(bin.buffer, off, n);
      case 5122: return new Int16Array(bin.buffer, off, n);
      case 5121: return new Uint8Array(bin.buffer, off, n);
    }
    throw new Error('componentType ' + a.componentType);
  }

  /* ------------------------------------------------------------- shaders */
  var VS = [
    'attribute vec3 aPos;',
    'attribute vec3 aNrm;',
    'uniform mat4 uProj, uView;',
    'varying vec3 vN, vP;',
    'void main(){',
    '  vN = aNrm; vP = aPos;',
    '  gl_Position = uProj * uView * vec4(aPos, 1.0);',
    '}'
  ].join('\n');

  var FS = [
    'precision mediump float;',
    'varying vec3 vN, vP;',
    'uniform vec3 uColor, uEye;',
    'uniform float uFlat;',
    'void main(){',
    '  if (uFlat > 0.5) { gl_FragColor = vec4(uColor, 1.0); return; }',
    '  vec3 N = normalize(vN);',
    '  vec3 V = normalize(uEye - vP);',
    '  if (dot(N, V) < 0.0) N = -N;',           // robust for open/flipped shells
    '  vec3 L1 = normalize(vec3( 0.45, 0.85,  0.55));',
    '  vec3 L2 = normalize(vec3(-0.65, 0.25, -0.40));',
    '  float d1 = max(dot(N, L1), 0.0);',
    '  float d2 = max(dot(N, L2), 0.0);',
    '  float hemi = 0.5 + 0.5 * N.y;',
    '  vec3 sky = vec3(0.96, 0.95, 0.94);',
    '  vec3 gnd = vec3(0.60, 0.59, 0.58);',
    '  vec3 amb = mix(gnd, sky, hemi) * 0.46;',
    '  vec3 H = normalize(L1 + V);',
    '  float spec = pow(max(dot(N, H), 0.0), 42.0) * 0.30;',
    '  float rim  = pow(1.0 - max(dot(N, V), 0.0), 3.0) * 0.16;',
    '  vec3 col = uColor * (amb + 0.62 * d1 + 0.22 * d2) + spec + rim;',
    '  col = pow(clamp(col, 0.0, 1.0), vec3(0.4545));',
    '  gl_FragColor = vec4(col, 1.0);',
    '}'
  ].join('\n');

  function compile(gl, type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }

  /* ------------------------------------------------------------- viewer */
  function init(root) {
    var canvas = root.querySelector('.cad__stage');
    var status = root.querySelector('.cad__status');
    var reset  = root.querySelector('.cad__reset');
    var src    = root.getAttribute('data-model');
    if (!canvas || !src) return;

    function fail(msg) { if (status) { status.textContent = msg; status.classList.remove('is-gone'); } }

    var gl = canvas.getContext('webgl2', { antialias: true, alpha: false }) ||
             canvas.getContext('webgl',  { antialias: true, alpha: false });
    if (!gl) { fail('3D preview unavailable'); return; }
    var isGL2 = (typeof WebGL2RenderingContext !== 'undefined') && (gl instanceof WebGL2RenderingContext);
    if (!isGL2) gl.getExtension('OES_element_index_uint');

    var prog = gl.createProgram();
    gl.attachShader(prog, compile(gl, gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, compile(gl, gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) { fail('3D preview unavailable'); return; }
    gl.useProgram(prog);

    var aPos = gl.getAttribLocation(prog, 'aPos');
    var aNrm = gl.getAttribLocation(prog, 'aNrm');
    var uProj = gl.getUniformLocation(prog, 'uProj');
    var uView = gl.getUniformLocation(prog, 'uView');
    var uColor = gl.getUniformLocation(prog, 'uColor');
    var uEye = gl.getUniformLocation(prog, 'uEye');
    var uFlat = gl.getUniformLocation(prog, 'uFlat');

    var parts = [];
    var ready = false;

    /* ---- camera state ---- */
    var HOME = { theta: 0.85, phi: 1.17, radius: 2.28, tx: 0, ty: 0 };
    var cam = { theta: HOME.theta, phi: HOME.phi, radius: HOME.radius, tx: 0, ty: 0 };
    var want = { theta: HOME.theta, phi: HOME.phi, radius: HOME.radius, tx: 0, ty: 0 };
    var spin = true;
    var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function goHome() {
      want.theta = HOME.theta; want.phi = HOME.phi; want.radius = HOME.radius;
      want.tx = 0; want.ty = 0; spin = true;
      root.classList.remove('is-touched');
    }
    if (reset) reset.addEventListener('click', goHome);

    /* ---- pointer interaction ---- */
    var drag = null, pointers = {}, pinch = 0;

    function touched() { spin = false; root.classList.add('is-touched'); }

    canvas.addEventListener('pointerdown', function (e) {
      canvas.setPointerCapture(e.pointerId);
      pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
      drag = { x: e.clientX, y: e.clientY, pan: e.button === 2 || e.shiftKey };
      touched();
    });
    canvas.addEventListener('pointermove', function (e) {
      if (pointers[e.pointerId]) { pointers[e.pointerId].x = e.clientX; pointers[e.pointerId].y = e.clientY; }
      var ids = Object.keys(pointers);
      if (ids.length === 2) {
        var a = pointers[ids[0]], b = pointers[ids[1]];
        var d = Math.hypot(a.x - b.x, a.y - b.y);
        if (pinch) want.radius = clamp(want.radius * (pinch / d), 1.35, 8);
        pinch = d; drag = null; return;
      }
      if (!drag) return;
      var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      drag.x = e.clientX; drag.y = e.clientY;
      if (drag.pan) {
        want.tx -= dx * 0.0032 * want.radius;
        want.ty += dy * 0.0032 * want.radius;
      } else {
        want.theta -= dx * 0.0068;
        want.phi = clamp(want.phi - dy * 0.0058, 0.14, Math.PI - 0.14);
      }
    });
    function up(e) {
      delete pointers[e.pointerId];
      if (Object.keys(pointers).length < 2) pinch = 0;
      drag = null;
    }
    canvas.addEventListener('pointerup', up);
    canvas.addEventListener('pointercancel', up);
    canvas.addEventListener('contextmenu', function (e) { e.preventDefault(); });
    canvas.addEventListener('wheel', function (e) {
      e.preventDefault();
      touched();
      want.radius = clamp(want.radius * Math.exp(e.deltaY * 0.0011), 1.35, 8);
    }, { passive: false });

    function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }

    /* ---- resize ---- */
    function resize() {
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      var w = Math.max(1, Math.round(canvas.clientWidth * dpr));
      var h = Math.max(1, Math.round(canvas.clientHeight * dpr));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w; canvas.height = h;
        gl.viewport(0, 0, w, h);
      }
    }
    window.addEventListener('resize', resize);

    /* ---- draw ---- */
    var bg = [0.933, 0.925, 0.914];
    function frame() {
      resize();
      var k = reduced ? 1 : 0.12;
      if (spin && !reduced) want.theta += 0.0016;
      cam.theta  += (want.theta  - cam.theta)  * k;
      cam.phi    += (want.phi    - cam.phi)    * k;
      cam.radius += (want.radius - cam.radius) * k;
      cam.tx     += (want.tx     - cam.tx)     * k;
      cam.ty     += (want.ty     - cam.ty)     * k;

      var ct = [cam.tx, cam.ty, 0];
      var eye = [
        ct[0] + cam.radius * Math.sin(cam.phi) * Math.sin(cam.theta),
        ct[1] + cam.radius * Math.cos(cam.phi),
        ct[2] + cam.radius * Math.sin(cam.phi) * Math.cos(cam.theta)
      ];
      var aspect = canvas.width / Math.max(1, canvas.height);
      gl.uniformMatrix4fv(uProj, false, perspective(0.72, aspect, 0.05, 60));
      gl.uniformMatrix4fv(uView, false, lookAt(eye, ct, [0, 1, 0]));
      gl.uniform3fv(uEye, new Float32Array(eye));

      gl.clearColor(bg[0], bg[1], bg[2], 1);
      gl.enable(gl.DEPTH_TEST);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      // solids first, nudged back so the edge overlay sits cleanly on top
      gl.enable(gl.POLYGON_OFFSET_FILL);
      gl.polygonOffset(1.0, 1.0);
      gl.uniform1f(uFlat, 0.0);
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        if (p.lines) continue;
        gl.bindBuffer(gl.ARRAY_BUFFER, p.pos);
        gl.enableVertexAttribArray(aPos);
        gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ARRAY_BUFFER, p.nrm);
        gl.enableVertexAttribArray(aNrm);
        gl.vertexAttribPointer(aNrm, 3, gl.FLOAT, false, 0, 0);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, p.idx);
        gl.uniform3fv(uColor, p.color);
        gl.drawElements(gl.TRIANGLES, p.count, p.itype, 0);
      }
      gl.disable(gl.POLYGON_OFFSET_FILL);

      // B-rep edges
      gl.uniform1f(uFlat, 1.0);
      for (var j = 0; j < parts.length; j++) {
        var q = parts[j];
        if (!q.lines) continue;
        gl.bindBuffer(gl.ARRAY_BUFFER, q.pos);
        gl.enableVertexAttribArray(aPos);
        gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);
        gl.disableVertexAttribArray(aNrm);
        gl.vertexAttrib3f(aNrm, 0, 1, 0);
        gl.uniform3fv(uColor, q.color);
        gl.drawArrays(gl.LINES, 0, q.count);
      }
      requestAnimationFrame(frame);
    }

    /* ---- load ---- */
    fetch(src).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.arrayBuffer();
    }).then(function (buf) {
      var m = parseGLB(buf), g = m.json, bin = m.bin;
      var prims = g.meshes[0].primitives;
      for (var i = 0; i < prims.length; i++) {
        var pr = prims[i];
        var mat = g.materials[pr.material] || {};
        var bc = (mat.pbrMetallicRoughness && mat.pbrMetallicRoughness.baseColorFactor) || [0.78, 0.8, 0.86, 1];
        var P = accessorArray(g, bin, pr.attributes.POSITION);
        var bp = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, bp);
        gl.bufferData(gl.ARRAY_BUFFER, P, gl.STATIC_DRAW);

        if (pr.mode === 1) {                       // LINES — the CAD edge overlay
          parts.push({ pos: bp, lines: true, count: P.length / 3,
                       color: new Float32Array([bc[0], bc[1], bc[2]]) });
          continue;
        }

        var N = accessorArray(g, bin, pr.attributes.NORMAL);
        var I = accessorArray(g, bin, pr.indices);
        var bn = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, bn); gl.bufferData(gl.ARRAY_BUFFER, N, gl.STATIC_DRAW);
        var bi = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, bi); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, I, gl.STATIC_DRAW);

        parts.push({
          pos: bp, nrm: bn, idx: bi, count: I.length,
          itype: (I instanceof Uint32Array) ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT,
          color: new Float32Array([bc[0], bc[1], bc[2]])
        });
      }
      ready = true;
      if (status) status.classList.add('is-gone');
      requestAnimationFrame(frame);
    }).catch(function (err) {
      fail('Could not load the 3D model');
      if (window.console) console.warn('cadview:', err);
    });
  }

  /* ------------------------------------------------------------- boot */
  function boot() {
    var roots = Array.prototype.slice.call(document.querySelectorAll('[data-model]'));
    if (!roots.length) return;
    if (!('IntersectionObserver' in window)) { roots.forEach(init); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { io.unobserve(en.target); init(en.target); }
      });
    }, { rootMargin: '420px 0px' });
    roots.forEach(function (r) { io.observe(r); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
