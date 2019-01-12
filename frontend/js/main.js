osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    id: 'OSM',
    attribution: "OpenStreetmap"
})

aerial = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',{
    attribution: "Google Aerial",id:'aerial'
})
m = L.map('mymap', {
    center: [40, -92],
    zoom: 10,
    layers: [osm, aerial]
})

let basemaps = {
    "Aerial":aerial,
    "OpenStreetMap": osm
}
let drawnItems = L.geoJson().addTo(m)


let overlays = {
    'Drawn Geometries': drawnItems
}

L.control.layers(basemaps, overlays, {
    collapsed: false}
).addTo(m)



props = {
    'Location': {
        'type': 'text'
    },
    'Point Count': {
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
    ${Object.keys(props).map(k=>{
        return `<tr><th><label for='${k}'>${k.toUpperCase()}</th><td><input type='${props[k].type}' id='${k}' value='${properties[k]?properties[k]:""}'></td></tr>`
    }).join('')}</tbody>\
    </table>\
    </form>`
};

m.on('draw:created', function (event) {
    let layer = event.layer;
    let feature = layer.feature = layer.feature || {}
    feature.type='Feature'
    console.log(layer)
    feature.properties={}
    Object.keys(props).forEach(v => {
        feature.properties[v] = null
    })
    drawnItems.addLayer(layer)
})

drawnItems.bindPopup(popup, {
    className: 'editorPopup'
})

let popform = document.getElementById('popup-form')

// drawnItems.bindTooltip(function (layer,feature) {
//     return JSON.stringify(layer.feature.properties)
// })

m.on('popupopen', function(layer,feature) {
    console.log(layer, feature)
    let popup = document.querySelector('#editorsubmit')
    popup.addEventListener('click',function(e){
        console.log(e.target.toGeoJSON())
    });
  });


function popup(layer, feature){
    let div = L.DomUtil.create('div', 'edtiormenu')
    // let inp = template(feature.properties)
    let table = L.DomUtil.create('table')
    let tbody = L.DomUtil.create('tbody')
    table.appendChild(tbody)
    div.appendChild(table)
    Object.keys(props).forEach(e=>{
        let tr = L.DomUtil.create('tr')
        let th = L.DomUtil.create('th')
        let td = L.DomUtil.create('td')
        let label=L.DomUtil.create('label')
        let inp=L.DomUtil.create('input')
        th.appendChild(label)
        td.appendChild(inp)
        tr.appendChild(th)
        tr.appendChild(td)
        label.innerText=e
        inp.type=props[e].type
        inp.id=e
        inp.value=layer.feature.properties[e]
        inp.addEventListener('change',function(t){
            layer.feature.properties[e]=t.target.value
            console.log(layer.toGeoJSON())
        })
        tbody.appendChild(tr)
    })
    button = document.createElement('button')
    button.innerText='Hello'
    button.id="editorsubmit"
    div.append(button)
    return div
}

let geocoder = L.Control.geocoder({
    defaultMarkGeocode: false
})
.on('markgeocode', function(e) {
    let center = e.geocode.center
    m.flyTo(L.latLng(center.lat, center.lng),15);
}).addTo(m);