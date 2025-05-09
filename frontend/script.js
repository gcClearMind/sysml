let allNodes = [];
let allLinks = [];
let nodeTypeFilters = [];
let edgeTypeFilters = [];

window.onload = () => {
  fetchGraph();
  loadFilters();
};

// ==============================
// 获取 URL 中的节点 ID (?id=xxx)
// ==============================
function getNodeIdFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get('id');
}

// ==============================
// 获取图谱
// ==============================
async function fetchGraph() {
  const nodeId = getNodeIdFromUrl();

  if (nodeId) {
    console.log("加载单节点", nodeId);
    try {
      const res = await fetch(`http://localhost:11003/graph_node?id=${nodeId}`);
      const data = await res.json();

      allNodes = data.nodes || [];
      allLinks = data.links || [];

      drawGraph(allNodes, allLinks);

      if (allNodes.length > 0) {
        showNodeInfo(null, allNodes[0]);
      } else {
        alert(`节点 ${nodeId} 不存在！`);
      }
    } catch (error) {
      console.error("加载节点失败:", error);
    }

  } else {
    console.log("加载全图");

    try {
      const res = await fetch('http://localhost:11003/graph?limit=100');
      const data = await res.json();

      allNodes = data.nodes || [];
      allLinks = data.links || [];

      drawGraph(allNodes, allLinks);
    } catch (error) {
      console.error("加载图谱失败:", error);
    }
  }
}

// ==============================
// 渲染图谱
// ==============================
function drawGraph(filteredNodes, filteredLinks) {
  const svg = d3.select('#graph-container svg');
  svg.selectAll("*").remove();

  const width = svg.node().getBoundingClientRect().width;
  const height = svg.node().getBoundingClientRect().height;

  const container = svg.append("g");

  addArrowMarkers(svg); // 定义箭头

  const zoom = d3.zoom()
    .scaleExtent([0.1, 10])
    .on("zoom", (event) => container.attr("transform", event.transform));

  svg.call(zoom);
  svg.call(zoom.transform, d3.zoomIdentity);

  filteredNodes.forEach(n => n.id = String(n.id));
  filteredLinks.forEach(l => {
    l.source = String(l.source);
    l.target = String(l.target);
  });

  assignLinkIndex(filteredLinks);

  const simulation = d3.forceSimulation(filteredNodes)
    .force("link", d3.forceLink(filteredLinks).id(d => d.id).distance(150))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2));

  // ========= Links =========
  const linkGroup = container.append("g").attr("class", "links");

  const link = linkGroup.selectAll("path")
    .data(filteredLinks)
    .enter().append("path")
    .attr("stroke-width", 2)
    .attr("stroke", d => getRelationColor(d.relation))
    .attr("fill", "none")
    .attr("marker-end", "url(#arrow)");

  // ========= Link Texts =========
  const linkText = linkGroup.selectAll(".link-text")
    .data(filteredLinks)
    .enter().append("text")
    .attr("font-size", 8)
    .attr("fill", "#333")
    .attr("text-anchor", "middle")
    .attr("dy", -5)
    .text(d => d.relation || "未知关系");

  // ========= Nodes =========
  const nodeGroup = container.append("g").attr("class", "nodes");

  const node = nodeGroup.selectAll("circle")
    .data(filteredNodes)
    .enter().append("circle")
    .attr("r", 8)
    .attr("fill", d => d3.schemeCategory10[d.labels[0].length % 10])
    .on("click", showNodeInfo)
    .call(d3.drag()
      .on("start", (event, d) => dragstarted(event, d, simulation))
      .on("drag", dragged)
      .on("end", (event, d) => dragended(event, d, simulation)));

  const nodeText = nodeGroup.selectAll("text")
    .data(filteredNodes)
    .enter().append("text")
    .attr("font-size", 10)
    .attr("text-anchor", "middle")
    .attr("dy", "-10px")
    .attr("fill", "#000")
    .text(d => d.name && d.name !== "" ? d.name : (d.labels[0] || "未命名"));

  // ========= Simulation Tick =========
  simulation.on("tick", () => {
    link.attr("d", d => generateLinkPath(d));

    linkText
      .attr("x", d => (d.source.x + d.target.x) / 2)
      .attr("y", d => (d.source.y + d.target.y) / 2);

    node
      .attr("cx", d => d.x)
      .attr("cy", d => d.y);

    nodeText
      .attr("x", d => d.x)
      .attr("y", d => d.y);
  });
}

// ==============================
// 定义箭头
// ==============================
function addArrowMarkers(svg) {
  const defs = svg.append("defs");

  defs.append("marker")
    .attr("id", "arrow")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 18)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("fill", "#999");
}

// ==============================
// 不同关系颜色
// ==============================
function getRelationColor(relation) {
  const colorMap = {
    "supplier": "#FF6B6B",
    "client": "#6BCB77",
    "dependsOn": "#4D96FF",
    "refine": "#FFC75F",
    "default": "#999999"
  };

  return colorMap[relation] || colorMap["default"];
}

// ==============================
// 多边分组计算
// ==============================
function assignLinkIndex(links) {
  const linkGroups = {};

  links.forEach(link => {
    const key = `${link.source}-${link.target}`;
    if (!linkGroups[key]) {
      linkGroups[key] = [];
    }
    linkGroups[key].push(link);
  });

  Object.values(linkGroups).forEach(group => {
    group.forEach((link, idx) => {
      link.linkIndex = idx;
      link.totalLinks = group.length;
    });
  });
}

// ==============================
// 生成弯曲路径
// ==============================
function generateLinkPath(d) {
  const srcX = d.source.x;
  const srcY = d.source.y;
  const tgtX = d.target.x;
  const tgtY = d.target.y;

  const dx = tgtX - srcX;
  const dy = tgtY - srcY;
  const dr = Math.sqrt(dx * dx + dy * dy);

  const baseOffset = 40;
  const curveOffset = (d.linkIndex - (d.totalLinks - 1) / 2) * baseOffset;

  const normX = dx / dr;
  const normY = dy / dr;

  const mx = (srcX + tgtX) / 2 + (-normY) * curveOffset;
  const my = (srcY + tgtY) / 2 + normX * curveOffset;

  return `M${srcX},${srcY} Q${mx},${my} ${tgtX},${tgtY}`;
}

// ==============================
// 节点信息展示
// ==============================
function showNodeInfo(event, d) {
  const panel = document.getElementById('info-panel');
  panel.style.display = 'block';
  panel.innerHTML = `
    <h3>节点信息</h3>
    <p><strong>ID:</strong> ${d.id}</p>
    <p><strong>标签:</strong> ${d.labels.join(", ")}</p>
    <p><strong>名称:</strong> ${d.name}</p>
    <button onclick="location.href='index.html?id=${d.id}'">跳转查看</button>
  `;
}

// ==============================
// 拖拽逻辑
// ==============================
function dragstarted(event, d, simulation) {
  if (!event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}

function dragged(event, d) {
  d.fx = event.x;
  d.fy = event.y;
}

function dragended(event, d, simulation) {
  if (!event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}

// ==============================
// 筛选功能
// ==============================
function loadFilters() {
  fetch('http://localhost:11003/labels')
    .then(res => res.json())
    .then(data => {
      const nodeContainer = document.getElementById('nodeTypeFilters');
      nodeContainer.innerHTML = '';
      data.labels.forEach(label => {
        const div = document.createElement('div');
        div.innerHTML = `<label><input type="checkbox" value="${label}" checked onchange="updateNodeFilters()">${label}</label>`;
        nodeContainer.appendChild(div);
      });
      updateNodeFilters();
    });

  fetch('http://localhost:11003/relations')
    .then(res => res.json())
    .then(data => {
      const edgeContainer = document.getElementById('edgeTypeFilters');
      edgeContainer.innerHTML = '';
      data.relations.forEach(relation => {
        const div = document.createElement('div');
        div.innerHTML = `<label><input type="checkbox" value="${relation}" checked onchange="updateEdgeFilters()">${relation}</label>`;
        edgeContainer.appendChild(div);
      });
      updateEdgeFilters();
    });
}

function updateNodeFilters() {
  nodeTypeFilters = Array.from(document.querySelectorAll('#nodeTypeFilters input:checked')).map(cb => cb.value);
}

function updateEdgeFilters() {
  edgeTypeFilters = Array.from(document.querySelectorAll('#edgeTypeFilters input:checked')).map(cb => cb.value);
}

function toggleAllNodeFilters(selectAll) {
  document.querySelectorAll('#nodeTypeFilters input').forEach(cb => cb.checked = selectAll);
  updateNodeFilters();
}

function toggleAllEdgeFilters(selectAll) {
  document.querySelectorAll('#edgeTypeFilters input').forEach(cb => cb.checked = selectAll);
  updateEdgeFilters();
}

async function applyFilters() {
  if (nodeTypeFilters.length > 0 && edgeTypeFilters.length > 0) {
    alert("不能同时筛选节点和关系！");
    return;
  }

  let endpoint = '';
  let payload = {};

  if (nodeTypeFilters.length > 0) {
    endpoint = '/filter_nodes';
    payload = { nodeTypes: nodeTypeFilters };
  } else if (edgeTypeFilters.length > 0) {
    endpoint = '/filter_edges';
    payload = { edgeTypes: edgeTypeFilters };
  } else {
    alert("请至少选择一种类型！");
    return;
  }

  try {
    const res = await fetch(`http://localhost:11003${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    drawGraph(data.nodes, data.links);

  } catch (error) {
    console.error("筛选请求失败", error);
  }
}
// 打开路径推理弹窗
function openInferenceModal() {
  document.getElementById('inferenceModal').style.display = 'block';
  document.getElementById('modalBackground').style.display = 'block';
  loadLabelsForInference(); // 加载标签选项
}

// 关闭路径推理弹窗
function closeInferenceModal() {
  document.getElementById('inferenceModal').style.display = 'none';
  document.getElementById('modalBackground').style.display = 'none';
}

// 获取起始和目标标签后的推理路径
// 获取推理路径
async function submitInference() {
  const startLabel = document.getElementById('startLabel').value;
  const endLabel = document.getElementById('endLabel').value;

  try {
    const res = await fetch('http://localhost:11003/infer_path', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ startLabel, endLabel })
    });

    const data = await res.json();

    // 显示路径描述弹窗
    showPathDescription(data.pathDescriptions);

    // 关闭推理弹窗
    closeInferenceModal();
  } catch (error) {
    console.error("推理请求失败", error);
  }
}

let currentPage = 1;
let itemsPerPage = 5; // 每页显示的路径数量
let totalPages = 1; // 总页数
let descriptions = []; // 用于存储推理路径描述的全局变量
// 显示路径描述的弹窗
function showPathDescription(descriptionsData) {
  const pathModal = document.getElementById('pathModal');
  const pathDescription = document.getElementById('pathDescription');
  const paginationControls = document.getElementById('paginationControls');
  const pageIndicator = document.getElementById('pageIndicator');
    // 更新 descriptions
  descriptions = descriptionsData;
  // 清空现有内容
  pathDescription.innerHTML = '';
// 计算总页数
  totalPages = Math.ceil(descriptions.length / itemsPerPage);

  console.log(totalPages, itemsPerPage)
  // 显示当前页的路径描述
  const startIdx = (currentPage - 1) * itemsPerPage;
  const endIdx = Math.min(currentPage * itemsPerPage, descriptions.length);
  const currentPageData = descriptions.slice(startIdx, endIdx);

  currentPageData .forEach(desc => {
    const ruleColumn = document.createElement('div');
    ruleColumn.classList.add('rule-column');

    const pathColumn = document.createElement('div');
    pathColumn.classList.add('path-column');

    // 规则列
    const ruleTitle = document.createElement('a');
    ruleTitle.href = "javascript:void(0);";
    ruleTitle.style.color = "blue";
    ruleTitle.innerText = `规则: ${desc.rule}`;
    ruleTitle.onclick = () => openRuleDetail(desc);
    ruleColumn.appendChild(ruleTitle);

    // 路径列
    desc.paths.forEach(path => {
      const pathText = document.createElement('p');
      pathText.innerHTML = path;
      pathColumn.appendChild(pathText);
    });
    // 添加分隔线
    const separator = document.createElement('hr');
    pathColumn.appendChild(separator);

    // 将规则列和路径列放入弹窗
    pathDescription.appendChild(ruleColumn);
    pathDescription.appendChild(pathColumn);
  });

    // 更新分页信息
  pageIndicator.innerHTML = `第 ${currentPage} 页`;
  // 控制分页按钮的启用/禁用
  document.getElementById('prevPageBtn').disabled = currentPage === 1;
  document.getElementById('nextPageBtn').disabled = currentPage === totalPages;

  pathModal.style.display = 'block';
  document.getElementById('modalBackground').style.display = 'block';
}
function changePage(direction) {
  const newPage = currentPage + direction;

  // 确保页码在合法范围内
  if (newPage >= 1 && newPage <= totalPages) {
    currentPage = newPage;
    showPathDescription(descriptions); // 重新加载当前页的路径描述
  }
}
// 关闭路径描述弹窗
function closePathModal() {
  document.getElementById('pathModal').style.display = 'none';
  document.getElementById('modalBackground').style.display = 'none';
}


// 加载标签列表到下拉框
function loadLabelsForInference() {
  fetch('http://localhost:11003/labels')
    .then(res => res.json())
    .then(data => {
      const startSelect = document.getElementById('startLabel');
      const endSelect = document.getElementById('endLabel');
      startSelect.innerHTML = '';
      endSelect.innerHTML = '';

      data.labels.forEach(label => {
        const option1 = document.createElement('option');
        option1.value = label;
        option1.innerText = label;
        startSelect.appendChild(option1);

        const option2 = document.createElement('option');
        option2.value = label;
        option2.innerText = label;
        endSelect.appendChild(option2);
      });
    });
}

function openImportModal() {
  document.getElementById('importModal').style.display = 'block';
}

function closeImportModal() {
  document.getElementById('importModal').style.display = 'none';
}

document.getElementById('importForm').addEventListener('submit', function (e) {
  e.preventDefault();

  const fileInput = document.getElementById('importFile');
  const file = fileInput.files[0];

  if (!file) {
    alert('请选择一个 XML 文件');
    return;
  }

  if (!file.name.endsWith('.xml')) {
    alert('文件格式错误！请上传 XML 文件');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  fetch('http://localhost:11003/upload', {
    method: 'POST',
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      document.getElementById('importResult').innerText = data.message || '上传成功';
      closeImportModal(); // 可选，上传完成后关闭窗口
      alert(data.message || '上传成功！');
    })
    .catch(err => {
      console.error(err);
      document.getElementById('importResult').innerText = '上传失败';
    });
});

// Fetching available SWRL rules from the backend


function openRuleDetail(desc) {
  const modal = document.getElementById('ruleDetailModal');
  const content = document.getElementById('ruleDetailContent');
  const input = document.getElementById('relationInput');

  // 解析规则末尾默认关系
  const lastArrowIdx = desc.rule.lastIndexOf("->");
  const ruleHead = desc.rule.substring(0, lastArrowIdx).trim();
  const ruleTail = desc.rule.substring(lastArrowIdx + 2).trim(); // 例如 relation(?A, ?B)

  input.value = ruleTail.split("(")[0]; // 默认填 relation

  // 显示规则和路径
  content.innerHTML = `
    <p><strong>原始规则:</strong> ${desc.rule}</p>
    <p><strong>匹配路径:</strong></p>
    <div>${desc.paths.map(p => `<p>${p}</p>`).join("")}</div>
  `;

  // 保存当前规则体和变量名，用于构造新规则
  modal.dataset.ruleHead = ruleHead;
  modal.dataset.ruleTailArgs = ruleTail.substring(ruleTail.indexOf('(')); // 保留(?A, ?B)

  modal.style.display = 'block';
  document.getElementById('modalBackground').style.display = 'block';
}

function saveRelation() {
  const modal = document.getElementById('ruleDetailModal');
  const newRelation = document.getElementById('relationInput').value.trim();
  const ruleHead = modal.dataset.ruleHead;
  const ruleArgs = modal.dataset.ruleTailArgs;

  if (!newRelation) {
    alert("请输入新的关系名称！");
    return;
  }

  const newRule = `${ruleHead} -> ${newRelation}${ruleArgs}`;
  alert(`你定义的新规则为:\n${newRule}`);

  // TODO：可添加将此规则提交给后端的逻辑

  closeRuleDetailModal();
}

function closeRuleDetailModal() {
  document.getElementById('ruleDetailModal').style.display = 'none';
  document.getElementById('modalBackground').style.display = 'none';
}
