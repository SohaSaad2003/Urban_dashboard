function drawPieChart(elementId, data) {
    const values = data.values || data.data_values;

    if (!data || !data.labels || !values || values.length !== data.labels.length) {
        console.error("Invalid data for pie chart:", data);
        return;
    }

    if (values.every(val => val === 0)) {
        console.warn("All values are zero, cannot render pie chart");
        document.getElementById(elementId).innerHTML = "<p>لا توجد بيانات صالحة لعرض الرسم البياني</p>";
        return;
    }

    const trace = {
        labels: data.labels,
        values: values,
        type: 'pie',
        textinfo: 'label+percent',
        hoverinfo: 'label+value+percent',
        marker: {
            colors: ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        }
    };

    const layout = {
        margin: { t: 30, b: 30, l: 30, r: 30 },
        showlegend: true
    };

    Plotly.newPlot(elementId, [trace], layout);
}

function drawBarChart(elementId, data) {
    const values = data.values || data.data_values;

    if (!data || !data.labels || !values || values.length !== data.labels.length) {
        console.error("Invalid data for bar chart:", data);
        return;
    }

    if (values.every(val => val === 0)) {
        console.warn("All values are zero, cannot render bar chart");
        document.getElementById(elementId).innerHTML = "<p>لا توجد بيانات صالحة لعرض الرسم البياني</p>";
        return;
    }

    const trace = {
        x: values,
        y: data.labels,
        type: 'bar',
        orientation: 'h',
        text: values,
        textposition: 'auto',
        marker: {
            color: '#1f77b4'
        }
    };

    const layout = {
        margin: { t: 30, b: 30, l: 200, r: 30 },
        xaxis: {
            title: 'العدد',
            tickformat: ',d',
            rangemode: 'tozero'
        },
        yaxis: { 
            title: {
                text: 'الخدمة',
                standoff: 80,
                font: {
                    size: 14
                },
                y: 1
            },
            automargin: true,
            tickfont: {
                size: 12
            },
            ticklen: 5,
            tickwidth: 1,
            side: 'left',
            fixedrange: true
        }
    };

    Plotly.newPlot(elementId, [trace], layout);
}

function drawAreaChart(elementId, data) {
    const values = data.values || data.data_values;

    if (!data || !data.labels || !values || values.length !== data.labels.length) {
        console.error("Invalid data for area chart:", data);
        return;
    }

    if (values.every(val => val === 0)) {
        console.warn("All values are zero, cannot render area chart");
        document.getElementById(elementId).innerHTML = "<p>لا توجد بيانات صالحة لعرض الرسم البياني</p>";
        return;
    }

    const trace = {
        x: data.labels,
        y: values,
        type: 'scatter',
        fill: 'tozeroy',
        mode: 'lines+markers',
        text: values,
        textposition: 'top center',
        marker: { color: '#2ca02c' }
    };

    const layout = {
        margin: { t: 30, b: 50, l: 50, r: 30 },
        xaxis: { title: 'الشوارع' },
        yaxis: {
            title: 'العدد',
            rangemode: 'tozero'
        }
    };

    Plotly.newPlot(elementId, [trace], layout);
}

function drawMap(elementId, data) {
    if (!data || data.length === 0) {
        console.warn("No valid map data");
        document.getElementById(elementId).innerHTML = "<p>لا توجد بيانات صالحة لعرض الخريطة</p>";
        return;
    }

    const coords = data.map(item => item.coordinates);
    const lat = coords.map(coord => coord[1]);
    const lon = coords.map(coord => coord[0]);
    const amenities = data.map(item => item.amenity);
    const namesEn = data.map(item => item['name:en']);
    const namesAr = data.map(item => item['name:ar']);

    const trace = {
        type: 'scattermapbox',
        lon: lon,
        lat: lat,
        text: amenities,
        hoverinfo: 'text',
        hovertemplate: '<b>الاسم (عربي):</b> %{customdata[0]}<br><b>الاسم (إنجليزي):</b> %{customdata[1]}<br><b>الخدمة:</b> %{text}',
        customdata: namesAr.map((name, i) => [name, namesEn[i]]),
        mode: 'markers',
        marker: { size: 10, color: '#1f77b4' }
    };

    const layout = {
        mapbox: {
            style: 'open-street-map',
            center: {
                lat: lat.length > 0 ? lat.reduce((a, b) => a + b, 0) / lat.length : 0,
                lon: lon.length > 0 ? lon.reduce((a, b) => a + b, 0) / lon.length : 0
            },
            zoom: 10
        },
        margin: { t: 0, b: 0, l: 0, r: 0 },
        height: 400
    };

    Plotly.newPlot(elementId, [trace], layout);
}

function exportPlot(elementId, filename) {
    Plotly.downloadImage(elementId, {
        format: 'png',
        filename: filename
    });
}
