

baseProps = {
    'id': {
        'type': 'text'
    },
    'NameBrand': {
        'type': 'text'
    },
    'Address': {
        'type': 'text'
    },
    'Type': {
        'type': 'text'
    },
    'NameBrand': {
        'type': 'text'
    }
}

let vm = new Vue({
    el: "#container",
    delimiters: ["{*", "*}"],
    data: {
        work: [{ id: null, address: null }],
        currentAssignment: Object.keys(baseProps).reduce((a, i) => Object.assign({ [i]: null }, a), {}),
        editorName: null
    },
    created: function () {
        this.fetchWork();
        this.timer = setInterval(this.fetchWork, 20000)
    },
    methods: {
        fetchWork: async function () {
            let caller = fetch('api/workflow')
                .then(r => r.json())
                .catch(e => console.log(e))
            this.work = await caller
        },
        cancelAutoUpdate: function () { clearInterval(this.timer) },
        assignGeocode: function (id, Address, Name, priority) {
            if (this.currentAssignment.id === null) {
                this.currentAssignment = { id: id, Address: Address, NameBrand: Name, priority: priority }
                this.work = this.work.filter(i => i.id != this.currentAssignment.id)
                fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(Address)}&limit=5&format=json&addressdetails=1`)
                    .then(r => r.json())
                    .catch(e => console.log(e))
                    .then(r => {
                        if (r.length > 0) {
                            m.flyTo([Number(r[0].lat), Number(r[0].lon)], 17)
                            setTimeout(updateProdContent, 1500)
                        }
                    })
                fetch(`/api/assignments/assign`, {
                    method: 'POST',
                    body: JSON.stringify({ id: id, editor: vm.editorName })
                }).catch(e => console.log(e))
            } else {
                alert('Finish or discard the current assignment before continuing.')
            }
        },
        dropCurrentEdit: function () {
            fetch(`/api/assignments/drop`, {
                method: 'POST',
                body: JSON.stringify({ id: this.currentAssignment.id })
            }).catch(e => console.log(e))
            this.currentAssignment = { id: null, Address: null, NameBrand: null, priority: null }
        }
    },
    beforeDestroy() {
        clearInterval(this.timer)
    }
})



osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    id: 'OSM',
    attribution: "OpenStreetmap"
})

aerial = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
    attribution: "Google Aerial",
    id: 'aerial'
})

m = L.map('mymap', {
    center: [33.615061, -84.470324],
    zoom: 10,
    layers: [osm, aerial]
})

let basemaps = {
    "Aerial": aerial,
    "OpenStreetMap": osm
}

drawnItems = L.geoJson().addTo(m)


production = L.geoJson(null, {
    style: function (feature) {
        return {
            fillColor: feature.properties.Status == 'Production' ? 'green' : 'yellow',
            color: 'black',
            fillOpacity: 0.6,
            weight: 2,
            dashArray: "10 5"
        }
    }
})
    .bindTooltip(function (layer) {
        let props = layer.feature.properties
        return `<table><tbody>${Object.keys(props).map(k => `<tr><th>${k}</th><td>${props[k]}</td></tr>`
        ).join('')}</tbody></table>`
    }, {
            sticky: true, className: 'geotooltip'
        })
    .addTo(m)

let overlays = {
    'Existing Geofences': production,
    'Current Feature Edit': drawnItems
}

L.control.layers(basemaps, overlays, {
    collapsed: false
}).addTo(m)





m.addControl(new L.Control.Draw({
    edit: {
        featureGroup: drawnItems,
        poly: {
            allowIntersection: false
        }
    },
    draw: {
        polygon: {
            allowIntersection: false,
            showArea: true
        }
    }
}))

var template = function (properties) {
    return `<form id="popup-form">\
    <table>\
    <tbody>\
    ${Object.keys(baseProps).map(k => {
        return `<tr><th><label for='${k}'>${k.toUpperCase()}</th><td><input type='${baseProps[k].type}' id='${k}' value='${properties[k] ? properties[k] : ""}'></td></tr>`
    }).join('')}</tbody>\
    </table>\
    </form>`
};

m.on('draw:created', function (event) {
    let layer = event.layer;
    let feature = layer.feature = layer.feature || {}
    feature.type = 'Feature'
    feature.properties = {}
    Object.keys(baseProps).forEach(v => {
        feature.properties[v] = null
    })
    drawnItems.addLayer(layer)
})




function updateProdContent() {
    fetch('api/stagedpolys', {
        method: 'POST',
        body: JSON.stringify({
            'polybound': buildPolyFromBounds(m.getBounds())
        })
    })
        .then(r => r.json())
        .catch(e => console.log(e))
        .then(r => {
            production.clearLayers()
            production.addData(r)
        })
}

function buildPolyFromBounds(bnds) {
    return `POLYGON((${bnds.getWest()} ${bnds.getSouth()}, \
${bnds.getEast()} ${bnds.getSouth()}, \
${bnds.getEast()} ${bnds.getNorth()}, \
${bnds.getWest()} ${bnds.getNorth()}, \
${bnds.getWest()} ${bnds.getSouth()}))`
}

let popform = document.getElementById('popup-form')

m.on('popupopen', function (layer, feature) {
    let popup = document.querySelector('#editorsubmit')
    popup.addEventListener('click', function (e) {
        m.closePopup()
        fetch('api/edits', {
            'method': 'POST',
            'body': JSON.stringify({ 'geojson': activeGeoJSON })
        })
        setTimeout(function () {
            drawnItems.clearLayers()
            updateProdContent()
        }, 700)
        Object.keys(baseProps).forEach(k => {
            vm.$set(vm.currentAssignment, k, null)
        })
    });
});

let activeGeoJSON;

function popup(layer, feature) {
    activeGeoJSON = layer.toGeoJSON()
    let div = L.DomUtil.create('div', 'editormenu')
    let table = L.DomUtil.create('table')
    let tbody = L.DomUtil.create('tbody')
    table.appendChild(tbody)
    div.appendChild(table)
    Object.keys(baseProps).forEach(e => {
        let tr = L.DomUtil.create('tr')
        let th = L.DomUtil.create('th')
        let td = L.DomUtil.create('td')
        let label = L.DomUtil.create('label')
        let inp = L.DomUtil.create('input')
        inp.type = baseProps[e].type
        inp.defaultValue = vm.currentAssignment[e]
        inp.value = vm.currentAssignment[e]
        th.appendChild(label)
        td.appendChild(inp)
        tr.appendChild(th)
        tr.appendChild(td)
        label.innerText = e
        inp.id = e
        layer.feature.properties[e] = inp.value
        activeGeoJSON = layer.toGeoJSON()
        // inp.value = layer.feature.properties[e]
        inp.addEventListener('change', function (t) {
            layer.feature.properties[e] = t.target.value;
            activeGeoJSON = layer.toGeoJSON()
        })
        tbody.appendChild(tr)
    })
    button = document.createElement('button')
    button.innerText = 'Submit'
    button.id = "editorsubmit"
    div.append(button)
    return div
}

drawnItems.bindPopup(popup, {
    className: 'editorPopup'
})


let uiController = L.control({ collapsed: false })

uiController.onAdd = function (m) {
    this._div = L.DomUtil.create('div', 'uicontrol')
    this.update()
    return this._div
}

uiController.update = function (props) {
    let button = L.DomUtil.create('button')
    button.id = "updatecontent"
    button.innerText = 'Update Map Content'
    this._div.appendChild(button)
    let prod = L.DomUtil.create('div', 'legend')
    prod.id = 'prod'; prod.innerText = 'Production'
    let staged = L.DomUtil.create('div', 'legend')
    staged.id = 'staged'; staged.innerText = 'Staged'
    this._div.appendChild(prod)
    this._div.appendChild(staged)
    let coordinput = L.DomUtil.create('input')
    coordinput.id = 'coordinput';
    coordinput.type = 'text'; coordinput.placeholder = 'Input Coordinates';
    this._div.appendChild(coordinput)
}



uiController.addTo(m)

let geocoder = L.Control.geocoder({
    defaultMarkGeocode: false
})
    .on('markgeocode', function (e) {
        let center = e.geocode.center
        m.flyTo(L.latLng(center.lat, center.lng), 15);
    }).addTo(m);

let buttoncontent = document.querySelector('#updatecontent')

buttoncontent.addEventListener('click', function () {
    updateProdContent()
})

let coordinateinput = document.querySelector('#coordinput')

coordinateinput.addEventListener('change', function (e) {
    try {
        coords = e.target.value.split(',').map(i => Number(i.trim()))
        m.flyTo(coords, 15)
    }
    catch (error) {
        alert("Invalid Coordinate input")
    }
})

vm.editorName = prompt('Enter your editor name: ').replace(/\s|;|/g, '')
