osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    id: 'OSM',
    attribution: "OpenStreetmap"
})

aerial = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
    attribution: "Google Aerial",
    id: 'aerial'
})

m = L.map('mymap', {
    center: [ 33.615061, -84.470324],
    zoom: 10,
    layers: [osm, aerial]
})

let basemaps = {
    "Aerial": aerial,
    "OpenStreetMap": osm
}

drawnItems = L.geoJson().addTo(m)

// staged = L.geoJson(null, {
//         style: function (feature) {
//             return {
//                 fillColor: 'red',
//                 color: 'black',
//                 dashArray: "30 10"
//             }
//         }
//     })
//     .bindTooltip(function (layer) {
//         let props = layer.feature.properties
//         return `<table><tbody>${Object.keys(props).map(k=>`<tr><th>${k}</th><td>${props[k]}</td></tr>`
//     ).join('')}</tbody></table>`
//     }, {
//         sticky: true
//     })
//     .addTo(m)

production = L.geoJson(null, {
        style: function (feature) {
            return {
                fillColor: feature.properties.Status=='Production'?'green':'yellow',
                color: 'black',
                fillOpacity: 0.6,
                weight: 2,
                dashArray: "10 5"
            }
        }
    })
    .bindTooltip(function (layer) {
        let props = layer.feature.properties
        return `<table><tbody>${Object.keys(props).map(k=>`<tr><th>${k}</th><td>${props[k]}</td></tr>`
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



baseProps = {
    'Location': {
        'type': 'text'
    },
    'Age': {
        'type': 'number'
    },
    'NameBrand': {
        'type': 'text'
    },
    'Date Entered': {
        'type': 'date'
    }
}

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
    console.log(layer)
    feature.properties = {}
    Object.keys(baseProps).forEach(v => {
        feature.properties[v] = null
    })
    drawnItems.addLayer(layer)
})

drawnItems.bindPopup(popup, {
    className: 'editorPopup'
})

let response = null;


function updateProdContent(){
    fetch('api/stagedpolys', {
        method: 'POST',
        body: JSON.stringify({
            'polybound': buildPolyFromBounds(m.getBounds())
        })
    })
    .then(r=>r.json())
    .catch(e=>console.log(e))
    .then(r=>{
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
        fetch('api/edits',{
            'method': 'POST',
            'body': JSON.stringify({'geojson':activeGeoJSON})
        })
        drawnItems.clearLayers()
        updateProdContent()
    });
});

let activeGeoJSON;

function popup(layer, feature) {
    activeGeoJSON = layer.toGeoJSON()
    let div = L.DomUtil.create('div', 'edtiormenu')
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
        th.appendChild(label)
        td.appendChild(inp)
        tr.appendChild(th)
        tr.appendChild(td)
        label.innerText = e
        inp.type = baseProps[e].type
        inp.id = e
        inp.value = layer.feature.properties[e]
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


let uiController = L.control({collapsed: false})

uiController.onAdd = function(m){
    this._div = L.DomUtil.create('div', 'uicontrol')
    this.update()
    return this._div
}

uiController.update = function(props){
    let button = L.DomUtil.create('button')
    button.id = "updatecontent"
    button.innerText = 'Update Map Content'
    this._div.appendChild(button)
    let prod = L.DomUtil.create('div', 'legend')
    prod.id = 'prod'; prod.innerText = 'Production'
    let staged = L.DomUtil.create('div', 'legend')
    staged.id='staged'; staged.innerText = 'Staged'
    this._div.appendChild(prod)
    this._div.appendChild(staged)
    let coordinput = L.DomUtil.create('input')
    coordinput.id='coordinput';
    coordinput.type='text'; coordinput.placeholder='Input Coordinates';
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

buttoncontent.addEventListener('click', function(){
    updateProdContent()
})

let coordinateinput = document.querySelector('#coordinput')

coordinateinput.addEventListener('change', function(e){
    try {
        coords = e.target.value.split(',').map(i=>Number(i.trim()))
        m.flyTo(coords, 15)
    }
    catch(error){
        console.log("Invalid Coordinate input")
    }
})