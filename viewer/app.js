(() => {
  "use strict";

  const INDEX_URL = "../graph/concept-index.json";
  const SCALE_ORDER = [
    "unit",
    "tile",
    "die",
    "package",
    "node",
    "rack",
    "cluster",
    "datacenter",
    "ecosystem",
  ];
  const STATUS_ORDER = ["seed", "draft", "verified", "deprecated"];
  const LAYER_COLORS = [
    "#3f7cac",
    "#8f5f9f",
    "#cb6f3f",
    "#43865f",
    "#b78b2f",
    "#5b6ea6",
    "#bf4f73",
    "#4f8b8b",
    "#7d6f5b",
    "#7067a8",
  ];

  const state = {
    data: null,
    nodes: [],
    edges: [],
    nodeById: new Map(),
    layerColors: new Map(),
    selectedId: null,
    filters: {
      layers: new Set(),
      scaleScopes: new Set(),
      statuses: new Set(),
      search: "",
    },
    visibleNodes: [],
    visibleNodeIds: new Set(),
    visibleEdges: [],
    visibleLinks: [],
    transform: { x: 0, y: 0, k: 1 },
    size: { width: 900, height: 640 },
    alpha: 0,
    frameId: 0,
    dragging: null,
    panning: null,
    hasUserMovedView: false,
  };

  const dom = {};

  document.addEventListener("DOMContentLoaded", init);

  async function init() {
    cacheDom();
    bindChrome();
    measureStage();
    observeResize();

    try {
      const response = await fetch(INDEX_URL, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      hydrateData(data);
      renderFilters();
      applyFilters();
      selectDefaultNode();
      fitGraph();
      startSimulation(0.75);
    } catch (error) {
      showLoadError(error);
    }
  }

  function cacheDom() {
    dom.svg = document.getElementById("graphSvg");
    dom.viewport = document.getElementById("graphViewport");
    dom.edgeLayer = document.getElementById("edgeLayer");
    dom.nodeLayer = document.getElementById("nodeLayer");
    dom.emptyState = document.getElementById("emptyState");
    dom.searchInput = document.getElementById("searchInput");
    dom.resetFilters = document.getElementById("resetFilters");
    dom.layerFilters = document.getElementById("layerFilters");
    dom.scaleFilters = document.getElementById("scaleFilters");
    dom.statusFilters = document.getElementById("statusFilters");
    dom.visibleNodeCount = document.getElementById("visibleNodeCount");
    dom.visibleEdgeCount = document.getElementById("visibleEdgeCount");
    dom.detailsTitle = document.getElementById("detailsTitle");
    dom.detailsHref = document.getElementById("detailsHref");
    dom.detailsBody = document.getElementById("detailsBody");
    dom.zoomIn = document.getElementById("zoomIn");
    dom.zoomOut = document.getElementById("zoomOut");
    dom.fitGraph = document.getElementById("fitGraph");
  }

  function bindChrome() {
    dom.searchInput.addEventListener("input", () => {
      state.filters.search = dom.searchInput.value.trim().toLowerCase();
      applyFilters();
    });

    dom.resetFilters.addEventListener("click", resetFilters);
    dom.fitGraph.addEventListener("click", () => {
      state.hasUserMovedView = true;
      fitGraph();
    });
    dom.zoomIn.addEventListener("click", () => zoomAtCenter(1.22));
    dom.zoomOut.addEventListener("click", () => zoomAtCenter(1 / 1.22));

    dom.svg.addEventListener(
      "wheel",
      (event) => {
        event.preventDefault();
        const factor = event.deltaY < 0 ? 1.12 : 1 / 1.12;
        zoomAtPointer(event, factor);
      },
      { passive: false },
    );

    dom.svg.addEventListener("pointerdown", startPan);
    dom.svg.addEventListener("pointermove", continuePointerAction);
    dom.svg.addEventListener("pointerup", finishPointerAction);
    dom.svg.addEventListener("pointercancel", finishPointerAction);

    dom.nodeLayer.addEventListener("pointerdown", startNodeDrag);
    dom.nodeLayer.addEventListener("click", (event) => {
      const nodeGroup = event.target.closest(".node");
      if (nodeGroup) {
        selectNode(nodeGroup.dataset.id);
      }
    });
  }

  function observeResize() {
    const resizeObserver = new ResizeObserver(() => {
      const oldWidth = state.size.width;
      const oldHeight = state.size.height;
      measureStage();
      if (!state.hasUserMovedView && oldWidth && oldHeight) {
        fitGraph();
      }
      renderPositions();
    });
    resizeObserver.observe(dom.svg);
  }

  function measureStage() {
    const rect = dom.svg.getBoundingClientRect();
    state.size.width = Math.max(320, rect.width || dom.svg.clientWidth || 900);
    state.size.height = Math.max(320, rect.height || dom.svg.clientHeight || 640);
  }

  function hydrateData(data) {
    const rawNodes = Array.isArray(data?.nodes) ? data.nodes : [];
    const rawEdges = Array.isArray(data?.edges) ? data.edges : [];
    const layers = sortLayers(unique(rawNodes.map((node) => valueOrUnknown(node.layer))));

    state.data = data;
    state.layerColors = new Map(
      layers.map((layer, index) => [layer, LAYER_COLORS[index % LAYER_COLORS.length]]),
    );

    state.nodes = rawNodes.map((node, index) => ({
      aliases: asArray(node.aliases),
      concept_type: valueOrEmpty(node.concept_type),
      degree: 0,
      granularity: valueOrEmpty(node.granularity),
      href: valueOrEmpty(node.href),
      id: valueOrUnknown(node.id),
      index,
      layer: valueOrUnknown(node.layer),
      layer_path: valueOrEmpty(node.layer_path),
      parent: valueOrEmpty(node.parent),
      path: valueOrEmpty(node.path),
      reasoning_roles: asArray(node.reasoning_roles),
      scale_scope: asArray(node.scale_scope),
      secondary_layers: asArray(node.secondary_layers),
      source_refs: asArray(node.source_refs),
      sources: asArray(node.sources),
      status: valueOrUnknown(node.status),
      tags: asArray(node.tags),
      title: valueOrUnknown(node.title || node.id),
      vx: 0,
      vy: 0,
      x: 0,
      y: 0,
    }));

    state.nodeById = new Map(state.nodes.map((node) => [node.id, node]));

    state.edges = rawEdges
      .map((edge, index) => ({
        confidence: valueOrEmpty(edge.confidence),
        index,
        notes: valueOrEmpty(edge.notes),
        source: valueOrUnknown(edge.source),
        target: valueOrUnknown(edge.target),
        type: valueOrUnknown(edge.type),
        offset: 0,
      }))
      .filter((edge) => state.nodeById.has(edge.source) && state.nodeById.has(edge.target));

    state.edges.forEach((edge) => {
      state.nodeById.get(edge.source).degree += 1;
      state.nodeById.get(edge.target).degree += 1;
    });

    state.nodes.forEach((node) => {
      node.radius = Math.max(9, Math.min(20, 8 + Math.sqrt(node.degree || 1) * 2.3));
    });

    assignEdgeOffsets();
    placeNodes();
  }

  function assignEdgeOffsets() {
    const byPair = new Map();
    state.edges.forEach((edge) => {
      const pair = [edge.source, edge.target].sort().join("|");
      const bucket = byPair.get(pair) || [];
      bucket.push(edge);
      byPair.set(pair, bucket);
    });

    byPair.forEach((bucket) => {
      const center = (bucket.length - 1) / 2;
      bucket.forEach((edge, index) => {
        edge.offset = (index - center) * 6;
      });
    });
  }

  function placeNodes() {
    const layers = sortLayers(unique(state.nodes.map((node) => node.layer)));
    const groups = new Map(layers.map((layer) => [layer, []]));
    state.nodes.forEach((node) => {
      groups.get(node.layer).push(node);
    });

    const marginX = 110;
    const marginY = 100;
    const usableWidth = Math.max(1, state.size.width - marginX * 2);
    const usableHeight = Math.max(1, state.size.height - marginY * 2);

    layers.forEach((layer, layerIndex) => {
      const nodes = groups.get(layer);
      const layerRatio = layers.length === 1 ? 0.5 : layerIndex / (layers.length - 1);
      const x = marginX + usableWidth * layerRatio;

      nodes
        .sort((a, b) => a.title.localeCompare(b.title))
        .forEach((node, index) => {
          const rowRatio = nodes.length === 1 ? 0.5 : index / (nodes.length - 1);
          const jitter = ((node.index % 5) - 2) * 12;
          node.x = x + jitter;
          node.y = marginY + usableHeight * rowRatio + ((node.index % 3) - 1) * 18;
          node.targetX = x;
        });
    });
  }

  function renderFilters() {
    const layerValues = sortLayers(unique(state.nodes.map((node) => node.layer)));
    const scaleValues = sortByScaleOrder(
      unique(state.nodes.flatMap((node) => node.scale_scope)),
    );
    const statusValues = sortByStatusOrder(unique(state.nodes.map((node) => node.status)));

    renderFilterGroup(dom.layerFilters, "layers", layerValues, layerCount, layerLabel);
    renderFilterGroup(dom.scaleFilters, "scaleScopes", scaleValues, scaleCount);
    renderFilterGroup(dom.statusFilters, "statuses", statusValues, statusCount);
  }

  function renderFilterGroup(container, groupName, values, countFn, labelFn = identity) {
    container.replaceChildren(
      ...values.map((value) => {
        const checkbox = createElement("input", {
          type: "checkbox",
          value,
          "data-group": groupName,
        });
        checkbox.addEventListener("change", handleFilterChange);

        const label = createElement(
          "label",
          { class: "check-row" },
          [
            checkbox,
            createElement("span", { class: "check-label" }, [
              groupName === "layers"
                ? createElement("span", {
                    class: "layer-swatch",
                    style: `background:${state.layerColors.get(value) || "#64748b"}`,
                  })
                : null,
              labelFn(value),
            ]),
            createElement("span", { class: "check-count" }, [String(countFn(value))]),
          ].filter(Boolean),
        );

        return label;
      }),
    );
  }

  function handleFilterChange(event) {
    const checkbox = event.currentTarget;
    const group = checkbox.dataset.group;
    const selected = state.filters[group];

    if (checkbox.checked) {
      selected.add(checkbox.value);
    } else {
      selected.delete(checkbox.value);
    }

    applyFilters();
  }

  function applyFilters() {
    state.visibleNodes = state.nodes.filter((node) => nodeMatchesFilters(node));
    state.visibleNodeIds = new Set(state.visibleNodes.map((node) => node.id));
    state.visibleEdges = state.edges.filter(
      (edge) => state.visibleNodeIds.has(edge.source) && state.visibleNodeIds.has(edge.target),
    );
    state.visibleLinks = buildSimulationLinks(state.visibleEdges);

    dom.visibleNodeCount.textContent = String(state.visibleNodes.length);
    dom.visibleEdgeCount.textContent = `${state.visibleEdges.length} edges`;

    if (state.selectedId && !state.visibleNodeIds.has(state.selectedId)) {
      state.selectedId = null;
    }

    renderGraph();
    renderDetails();
    updateEmptyState();
    if (!state.hasUserMovedView) {
      fitGraph();
    }
    startSimulation(0.75);
  }

  function nodeMatchesFilters(node) {
    const filters = state.filters;
    const matchesLayer = filters.layers.size === 0 || filters.layers.has(node.layer);
    const matchesStatus = filters.statuses.size === 0 || filters.statuses.has(node.status);
    const matchesScale =
      filters.scaleScopes.size === 0 ||
      node.scale_scope.some((scope) => filters.scaleScopes.has(scope));
    const matchesSearch = !filters.search || searchableText(node).includes(filters.search);

    return matchesLayer && matchesStatus && matchesScale && matchesSearch;
  }

  function searchableText(node) {
    return [
      node.id,
      node.title,
      node.layer,
      node.status,
      ...node.scale_scope,
      ...node.tags,
      ...node.reasoning_roles,
      ...node.sources,
    ]
      .join(" ")
      .toLowerCase();
  }

  function buildSimulationLinks(edges) {
    const seen = new Set();
    const links = [];

    edges.forEach((edge) => {
      const key = [edge.source, edge.target].sort().join("|");
      if (seen.has(key)) {
        return;
      }
      seen.add(key);
      links.push(edge);
    });

    return links;
  }

  function renderGraph() {
    dom.edgeLayer.replaceChildren();
    dom.nodeLayer.replaceChildren();

    const edgeElements = new Map();
    const edgeHitElements = new Map();
    state.visibleEdges.forEach((edge) => {
      const visibleLine = createSvgElement("line", {
        class: "edge",
        "data-confidence": edge.confidence,
      });
      const hitLine = createSvgElement("line", {
        class: "edge-hit",
        tabindex: "0",
      });
      hitLine.addEventListener("click", () => selectNode(edge.target));

      const title = createSvgElement("title");
      title.textContent = `${edge.source} -> ${edge.target} (${edge.type})`;
      visibleLine.append(title);

      dom.edgeLayer.append(visibleLine, hitLine);
      edgeElements.set(edge.index, visibleLine);
      edgeHitElements.set(edge.index, hitLine);
    });

    const nodeElements = new Map();
    state.visibleNodes.forEach((node) => {
      const group = createSvgElement("g", {
        class: `node${node.id === state.selectedId ? " is-selected" : ""}`,
        "data-id": node.id,
        "data-status": node.status,
        style: `--layer-color:${state.layerColors.get(node.layer) || "#64748b"}`,
        tabindex: "0",
      });
      const title = createSvgElement("title");
      title.textContent = `${node.title} (${node.id})`;
      const circle = createSvgElement("circle", { r: String(node.radius) });
      const label = createNodeLabel(node);
      group.append(title, circle, label.titleText, label.idText);
      group.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectNode(node.id);
        }
      });

      dom.nodeLayer.append(group);
      nodeElements.set(node.id, group);
    });

    state.edgeElements = edgeElements;
    state.edgeHitElements = edgeHitElements;
    state.nodeElements = nodeElements;
    renderPositions();
  }

  function createNodeLabel(node) {
    const lines = wrapLabel(node.title, 18, 2);
    const titleText = createSvgElement("text", { y: String(node.radius + 15) });
    lines.forEach((line, index) => {
      const tspan = createSvgElement("tspan", {
        x: "0",
        dy: index === 0 ? "0" : "13",
      });
      tspan.textContent = line;
      titleText.append(tspan);
    });

    const idText = createSvgElement("text", {
      class: "node-id",
      y: String(node.radius + 18 + lines.length * 13),
    });
    idText.textContent = node.id;

    return { titleText, idText };
  }

  function renderPositions() {
    if (!state.nodeElements || !state.edgeElements) {
      return;
    }

    state.visibleEdges.forEach((edge) => {
      const line = state.edgeElements.get(edge.index);
      const hitLine = state.edgeHitElements.get(edge.index);
      if (!line || !hitLine) {
        return;
      }

      const coords = edgeCoordinates(edge);
      setSvgAttrs(line, coords);
      setSvgAttrs(hitLine, coords);
    });

    state.visibleNodes.forEach((node) => {
      const group = state.nodeElements.get(node.id);
      if (group) {
        group.setAttribute("transform", `translate(${node.x.toFixed(2)} ${node.y.toFixed(2)})`);
        group.classList.toggle("is-selected", node.id === state.selectedId);
      }
    });

    dom.viewport.setAttribute(
      "transform",
      `translate(${state.transform.x.toFixed(2)} ${state.transform.y.toFixed(2)}) scale(${state.transform.k.toFixed(3)})`,
    );
  }

  function edgeCoordinates(edge) {
    const source = state.nodeById.get(edge.source);
    const target = state.nodeById.get(edge.target);
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const length = Math.max(1, Math.hypot(dx, dy));
    const ux = dx / length;
    const uy = dy / length;
    const nx = -uy;
    const ny = ux;
    const offset = edge.offset || 0;
    const sourcePad = source.radius + 4;
    const targetPad = target.radius + 9;

    return {
      x1: (source.x + ux * sourcePad + nx * offset).toFixed(2),
      y1: (source.y + uy * sourcePad + ny * offset).toFixed(2),
      x2: (target.x - ux * targetPad + nx * offset).toFixed(2),
      y2: (target.y - uy * targetPad + ny * offset).toFixed(2),
    };
  }

  function selectDefaultNode() {
    if (state.selectedId || state.visibleNodes.length === 0) {
      renderDetails();
      return;
    }

    const highestDegree = [...state.visibleNodes].sort((a, b) => b.degree - a.degree)[0];
    selectNode(highestDegree.id);
  }

  function selectNode(nodeId) {
    if (!state.nodeById.has(nodeId) || !state.visibleNodeIds.has(nodeId)) {
      return;
    }

    state.selectedId = nodeId;
    renderDetails();
    renderPositions();
  }

  function renderDetails() {
    const node = state.selectedId ? state.nodeById.get(state.selectedId) : null;

    if (!node) {
      dom.detailsTitle.textContent = "No concept selected";
      dom.detailsHref.hidden = true;
      dom.detailsHref.removeAttribute("href");
      dom.detailsBody.replaceChildren(
        createElement("p", { class: "details-empty" }, [
          state.visibleNodes.length ? "No concept selected." : "No concept matches the current view.",
        ]),
      );
      return;
    }

    dom.detailsTitle.textContent = node.title;
    if (node.href) {
      dom.detailsHref.href = `../${node.href}`;
      dom.detailsHref.hidden = false;
    } else {
      dom.detailsHref.hidden = true;
      dom.detailsHref.removeAttribute("href");
    }

    const outgoing = state.edges.filter((edge) => edge.source === node.id);
    const incoming = state.edges.filter((edge) => edge.target === node.id);

    dom.detailsBody.replaceChildren(
      detailSection("Identity", [
        fieldRow("Id", node.id),
        fieldRow("Status", node.status),
        fieldRow("Layer", node.layer),
        fieldRow("Layer Path", node.layer_path || node.layer),
        fieldRow("Parent", node.parent || "None"),
        fieldRow("Markdown", node.href || "None"),
      ]),
      detailSection("Scale Scope", [chipList(node.scale_scope)]),
      detailSection("Tags", [chipList(node.tags)]),
      detailSection("Reasoning Roles", [chipList(node.reasoning_roles)]),
      detailSection("Sources", [chipList([...new Set([...node.sources, ...node.source_refs])])]),
      detailSection("Outgoing Edges", [edgeList(outgoing, "outgoing")]),
      detailSection("Incoming Edges", [edgeList(incoming, "incoming")]),
    );
  }

  function detailSection(title, children) {
    return createElement("section", { class: "detail-section" }, [
      createElement("h3", {}, [title]),
      ...children,
    ]);
  }

  function fieldRow(label, value) {
    return createElement("div", { class: "field-row" }, [
      createElement("span", { class: "field-label" }, [label]),
      createElement("span", { class: "field-value" }, [value || "None"]),
    ]);
  }

  function chipList(values) {
    const chips = asArray(values);
    if (chips.length === 0) {
      return createElement("span", { class: "muted" }, ["None"]);
    }

    return createElement(
      "div",
      { class: "chip-list" },
      chips.map((value) =>
        createElement(
          "span",
          {
            class: "chip",
          },
          [value],
        ),
      ),
    );
  }

  function edgeList(edges, direction) {
    if (edges.length === 0) {
      return createElement("span", { class: "muted" }, ["None"]);
    }

    return createElement(
      "ul",
      { class: "edge-list" },
      edges.map((edge) => {
        const otherId = direction === "outgoing" ? edge.target : edge.source;
        const otherNode = state.nodeById.get(otherId);
        const link = createElement("a", { href: "#", "data-node-id": otherId }, [
          otherNode ? otherNode.title : otherId,
        ]);
        link.addEventListener("click", (event) => {
          event.preventDefault();
          if (state.visibleNodeIds.has(otherId)) {
            selectNode(otherId);
          }
        });

        return createElement("li", {}, [
          link,
          createElement("span", { class: "edge-meta" }, [
            `${edge.type}${edge.confidence ? ` / ${edge.confidence}` : ""}`,
          ]),
          edge.notes ? createElement("span", { class: "edge-note" }, [edge.notes]) : null,
        ]);
      }),
    );
  }

  function updateEmptyState() {
    if (!state.data || state.nodes.length === 0) {
      showEmptyState("No graph data", "The index loaded, but it does not contain concepts.");
      return;
    }

    if (state.visibleNodes.length === 0) {
      showEmptyState("No matching concepts", "Reset or adjust the active filters.");
      return;
    }

    dom.emptyState.hidden = true;
    dom.emptyState.replaceChildren();
  }

  function showLoadError(error) {
    dom.visibleNodeCount.textContent = "0";
    dom.visibleEdgeCount.textContent = "0 edges";
    dom.detailsTitle.textContent = "Graph unavailable";
    dom.detailsHref.hidden = true;
    dom.detailsBody.replaceChildren(
      createElement("p", { class: "details-empty" }, [
        "Unable to load ../graph/concept-index.json.",
      ]),
    );
    showEmptyState(
      "Unable to load graph data",
      `Open this viewer through a static server from knowledge-base. ${error.message}`,
    );
  }

  function showEmptyState(title, message) {
    dom.emptyState.hidden = false;
    dom.emptyState.replaceChildren(
      createElement("strong", {}, [title]),
      createElement("span", {}, [message]),
    );
  }

  function resetFilters() {
    state.filters.layers.clear();
    state.filters.scaleScopes.clear();
    state.filters.statuses.clear();
    state.filters.search = "";
    dom.searchInput.value = "";
    document
      .querySelectorAll('.check-row input[type="checkbox"]')
      .forEach((checkbox) => {
        checkbox.checked = false;
      });
    state.hasUserMovedView = false;
    applyFilters();
    selectDefaultNode();
    fitGraph();
  }

  function startSimulation(alpha) {
    state.alpha = Math.max(state.alpha, alpha);
    if (!state.frameId) {
      state.frameId = requestAnimationFrame(tick);
    }
  }

  function tick() {
    state.frameId = 0;
    if (state.alpha < 0.01 || state.visibleNodes.length === 0) {
      state.alpha = 0;
      return;
    }

    applyForces();
    renderPositions();
    state.alpha *= 0.92;
    state.frameId = requestAnimationFrame(tick);
  }

  function applyForces() {
    const nodes = state.visibleNodes;
    const alpha = state.alpha;
    const centerX = state.size.width / 2;
    const centerY = state.size.height / 2;

    nodes.forEach((node) => {
      if (state.dragging?.node === node) {
        return;
      }
      node.vx += (centerX - node.x) * 0.0009 * alpha;
      node.vy += (centerY - node.y) * 0.0009 * alpha;
      if (Number.isFinite(node.targetX)) {
        node.vx += (node.targetX - node.x) * 0.0022 * alpha;
      }
    });

    for (let i = 0; i < nodes.length; i += 1) {
      for (let j = i + 1; j < nodes.length; j += 1) {
        const a = nodes[i];
        const b = nodes[j];
        let dx = b.x - a.x;
        let dy = b.y - a.y;
        let distance = Math.hypot(dx, dy);
        if (distance < 1) {
          dx = (j - i) * 0.01;
          dy = 0.01;
          distance = 1;
        }

        const minDistance = a.radius + b.radius + 82;
        const force = Math.min(3.5, (minDistance * minDistance) / (distance * distance)) * alpha;
        const fx = (dx / distance) * force;
        const fy = (dy / distance) * force;
        a.vx -= fx;
        a.vy -= fy;
        b.vx += fx;
        b.vy += fy;
      }
    }

    state.visibleLinks.forEach((edge) => {
      const source = state.nodeById.get(edge.source);
      const target = state.nodeById.get(edge.target);
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const distance = Math.max(1, Math.hypot(dx, dy));
      const desired = 145;
      const force = (distance - desired) * 0.006 * alpha;
      const fx = (dx / distance) * force;
      const fy = (dy / distance) * force;

      if (state.dragging?.node !== source) {
        source.vx += fx;
        source.vy += fy;
      }
      if (state.dragging?.node !== target) {
        target.vx -= fx;
        target.vy -= fy;
      }
    });

    nodes.forEach((node) => {
      if (state.dragging?.node === node) {
        node.vx = 0;
        node.vy = 0;
        return;
      }

      node.vx *= 0.82;
      node.vy *= 0.82;
      node.x = clamp(node.x + node.vx, 36, state.size.width - 36);
      node.y = clamp(node.y + node.vy, 36, state.size.height - 36);
    });
  }

  function startNodeDrag(event) {
    const nodeGroup = event.target.closest(".node");
    if (!nodeGroup) {
      return;
    }

    event.stopPropagation();
    event.preventDefault();
    const node = state.nodeById.get(nodeGroup.dataset.id);
    if (!node) {
      return;
    }

    selectNode(node.id);
    const pointer = screenToGraph(event);
    state.dragging = {
      node,
      pointerId: event.pointerId,
      offsetX: node.x - pointer.x,
      offsetY: node.y - pointer.y,
    };
    nodeGroup.setPointerCapture(event.pointerId);
  }

  function startPan(event) {
    if (event.button !== 0 || event.target.closest(".node")) {
      return;
    }

    state.panning = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      x: state.transform.x,
      y: state.transform.y,
    };
    dom.svg.setPointerCapture(event.pointerId);
  }

  function continuePointerAction(event) {
    if (state.dragging && state.dragging.pointerId === event.pointerId) {
      const pointer = screenToGraph(event);
      state.dragging.node.x = pointer.x + state.dragging.offsetX;
      state.dragging.node.y = pointer.y + state.dragging.offsetY;
      state.dragging.node.targetX = state.dragging.node.x;
      renderPositions();
      startSimulation(0.12);
      return;
    }

    if (state.panning && state.panning.pointerId === event.pointerId) {
      state.transform.x = state.panning.x + event.clientX - state.panning.startX;
      state.transform.y = state.panning.y + event.clientY - state.panning.startY;
      state.hasUserMovedView = true;
      renderPositions();
    }
  }

  function finishPointerAction(event) {
    if (state.dragging && state.dragging.pointerId === event.pointerId) {
      const nodeGroup = state.nodeElements?.get(state.dragging.node.id);
      if (nodeGroup?.hasPointerCapture(event.pointerId)) {
        nodeGroup.releasePointerCapture(event.pointerId);
      }
      state.dragging = null;
      state.hasUserMovedView = true;
      startSimulation(0.22);
    }

    if (state.panning && state.panning.pointerId === event.pointerId) {
      if (dom.svg.hasPointerCapture(event.pointerId)) {
        dom.svg.releasePointerCapture(event.pointerId);
      }
      state.panning = null;
    }
  }

  function zoomAtCenter(factor) {
    const center = {
      x: state.size.width / 2,
      y: state.size.height / 2,
    };
    zoomAtScreenPoint(center.x, center.y, factor);
  }

  function zoomAtPointer(event, factor) {
    const rect = dom.svg.getBoundingClientRect();
    zoomAtScreenPoint(event.clientX - rect.left, event.clientY - rect.top, factor);
  }

  function zoomAtScreenPoint(screenX, screenY, factor) {
    const nextScale = clamp(state.transform.k * factor, 0.25, 3.4);
    const graphX = (screenX - state.transform.x) / state.transform.k;
    const graphY = (screenY - state.transform.y) / state.transform.k;
    state.transform.x = screenX - graphX * nextScale;
    state.transform.y = screenY - graphY * nextScale;
    state.transform.k = nextScale;
    state.hasUserMovedView = true;
    renderPositions();
  }

  function fitGraph() {
    if (state.visibleNodes.length === 0) {
      state.transform = { x: state.size.width / 2, y: state.size.height / 2, k: 1 };
      renderPositions();
      return;
    }

    const bounds = state.visibleNodes.reduce(
      (box, node) => ({
        minX: Math.min(box.minX, node.x - node.radius),
        minY: Math.min(box.minY, node.y - node.radius),
        maxX: Math.max(box.maxX, node.x + node.radius),
        maxY: Math.max(box.maxY, node.y + node.radius),
      }),
      { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity },
    );

    const pad = 76;
    const graphWidth = Math.max(1, bounds.maxX - bounds.minX + pad * 2);
    const graphHeight = Math.max(1, bounds.maxY - bounds.minY + pad * 2);
    const scale = Math.min(1.45, state.size.width / graphWidth, state.size.height / graphHeight);
    const graphCenterX = (bounds.minX + bounds.maxX) / 2;
    const graphCenterY = (bounds.minY + bounds.maxY) / 2;

    state.transform = {
      x: state.size.width / 2 - graphCenterX * scale,
      y: state.size.height / 2 - graphCenterY * scale,
      k: scale,
    };
    renderPositions();
  }

  function screenToGraph(event) {
    const rect = dom.svg.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left - state.transform.x) / state.transform.k,
      y: (event.clientY - rect.top - state.transform.y) / state.transform.k,
    };
  }

  function createElement(tag, attrs = {}, children = []) {
    const element = document.createElement(tag);
    setElementAttrs(element, attrs);
    appendChildren(element, children);
    return element;
  }

  function createSvgElement(tag, attrs = {}) {
    const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
    setSvgAttrs(element, attrs);
    return element;
  }

  function appendChildren(parent, children) {
    children.flat().forEach((child) => {
      if (child == null) {
        return;
      }
      if (child instanceof Node) {
        parent.append(child);
      } else {
        parent.append(document.createTextNode(String(child)));
      }
    });
  }

  function setElementAttrs(element, attrs) {
    Object.entries(attrs).forEach(([key, value]) => {
      if (value == null) {
        return;
      }
      if (key === "class") {
        element.setAttribute("class", value);
      } else if (key === "style") {
        element.setAttribute("style", value);
      } else if (key in element && key !== "list") {
        element[key] = value;
      } else {
        element.setAttribute(key, value);
      }
    });
  }

  function setSvgAttrs(element, attrs) {
    Object.entries(attrs).forEach(([key, value]) => {
      element.setAttribute(key, value);
    });
  }

  function wrapLabel(label, maxChars, maxLines) {
    const words = String(label).split(/\s+/).filter(Boolean);
    if (words.length === 0) {
      return [""];
    }

    const lines = [];
    let line = "";

    words.forEach((word) => {
      const next = line ? `${line} ${word}` : word;
      if (next.length > maxChars && line) {
        lines.push(line);
        line = word;
      } else {
        line = next;
      }
    });
    if (line) {
      lines.push(line);
    }

    if (lines.length <= maxLines) {
      return lines;
    }

    const kept = lines.slice(0, maxLines);
    kept[maxLines - 1] = trimWithEllipsis(kept[maxLines - 1], maxChars);
    return kept;
  }

  function trimWithEllipsis(value, maxChars) {
    if (value.length <= maxChars - 3) {
      return `${value}...`;
    }
    return `${value.slice(0, Math.max(1, maxChars - 3))}...`;
  }

  function asArray(value) {
    return Array.isArray(value) ? value.filter((item) => item != null).map(String) : [];
  }

  function valueOrUnknown(value) {
    return value == null || value === "" ? "unknown" : String(value);
  }

  function valueOrEmpty(value) {
    return value == null ? "" : String(value);
  }

  function unique(values) {
    return [...new Set(values.filter((value) => value != null && value !== ""))];
  }

  function sortLayers(layers) {
    return [...layers].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  }

  function sortByScaleOrder(values) {
    return [...values].sort((a, b) => {
      const indexA = SCALE_ORDER.indexOf(a);
      const indexB = SCALE_ORDER.indexOf(b);
      if (indexA === -1 && indexB === -1) {
        return a.localeCompare(b);
      }
      if (indexA === -1) {
        return 1;
      }
      if (indexB === -1) {
        return -1;
      }
      return indexA - indexB;
    });
  }

  function sortByStatusOrder(values) {
    return [...values].sort((a, b) => {
      const indexA = STATUS_ORDER.indexOf(a);
      const indexB = STATUS_ORDER.indexOf(b);
      if (indexA === -1 && indexB === -1) {
        return a.localeCompare(b);
      }
      if (indexA === -1) {
        return 1;
      }
      if (indexB === -1) {
        return -1;
      }
      return indexA - indexB;
    });
  }

  function layerLabel(value) {
    return value;
  }

  function layerCount(value) {
    return state.nodes.filter((node) => node.layer === value).length;
  }

  function scaleCount(value) {
    return state.nodes.filter((node) => node.scale_scope.includes(value)).length;
  }

  function statusCount(value) {
    return state.nodes.filter((node) => node.status === value).length;
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function identity(value) {
    return value;
  }
})();
