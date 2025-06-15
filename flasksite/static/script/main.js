//const GRADES = {"A+": 1, "A": 2, "B": 3, "C": 4, "D": 5, "F": 6};
//const GRADES = ["F", "D", "D+", "C", "C+", "B", "B+", "A", "X", "A+"];
const GRADES = ["F", "D", "C", "B", "A", "A+"];
const GRADE_COLOURS = {"A+": "#FF41D8", "A": "#2EC918", "B": "#23C5D5", "C": "#FF5400", "D": "#C40000", "F": "#000000"}
const COLOUR_TO_GRADE = Object.fromEntries(
	Object.entries(GRADE_COLOURS).map( ([k,v]) => [v, k])
);


async function getApiWeekOfDailySummaries(fcstTimeBufferDays, locId) {
	let query = `https://https://weather.gtweb.dev/api/results/daily?day_date=yesterday&countback_days=7&fcst_time_buffer_days=${fcstTimeBufferDays}`;

	if (locId) {
		query +=`&loc_id=${locId}`;
	};

	let response = await fetch(query);

	return (await response.json());
};

async function getApiMonthOfDailySummaries(fcstTimeBufferDays, locId) {
	let query = `https://weather.gtweb.dev/api/results/daily?day_date=yesterday&countback_days=${api.config.monthNDays}&fcst_time_buffer_days=${fcstTimeBufferDays}`;

	if (locId) {
		query +=`&loc_id=${locId}`;
	};

	let response = await fetch(query);

	return (await response.json());
};

async function getApiWeekOfDailyResultsOfFuture(futureTime, locId) {
	let query = `https://weather.gtweb.dev/api/results/daily?future_time=${futureTime}&loc_id${locId}`;

	let response = await fetch(query);

	return (await response.json());
};

async function getApiFcstsOfDay(locId) {
	let response = await fetch(`https://weather.gtweb.dev/api/weather/forecasts?loc_id=${locId}&day_date=yesterday&days=1`);

	return (await response.json());
};

async function getApiObsofDay(locId) {
	let response = await fetch(`https://weather.gtweb.dev/api/weather/obs?loc_id=${locId}&day_date=yesterday`);

	return (await response.json());
};

async function fetchSiteInfo(isDict) {
	isDict = Boolean(isDict);

	let response = await fetch(`https://weather.gtweb.dev/api/info/sites?dict=${isDict}`);

	let json = await response.json();

	if (isDict) {
		for (let v of Object.values(json)) {
			v.clean_name = v.clean_name.replace(/([a-z])([A-Z])/g, "$1 $2");
		};
	} else {
		for (let v of json) {
			v.clean_name = v.clean_name.replace(/([a-z])([A-Z])/g, "$1 $2");
		};
	};
	
	return json;
};







function actualInitMap({MapConstruct, MarkerConstruct, PinConstruct, selector, popup, grades, onPinSelect, data}={}) {
	function setScale(pin, newScale) {
		let currentTransform = pin.style.transform || "";
		pin.style.transform = currentTransform.replace(/scale\([\d\.]+\)/g, "") + `scale(${newScale})`;
	};

	if (!grades) grades = {"default": {}};

	const mapCont = document.querySelector(selector);
	mapCont.className = mapCont.className.replace("invisible","");

	let mapElem = new MapConstruct(mapCont, {
		zoom: 5,
		center: api.map.centre,
		mapId: api.map.id,
		mapTypeId: "roadmap",
		
		minZoom: 4.5,
		restriction: {
			latLngBounds: {
				north: 65,
				south: 45,
				east: 10,
				west: -20
			}
		},

		zoomControl: false,
		cameraControl: false,
		mapTypeControl: false,
		scaleControl: false,
		streetViewControl: false,
		rotateControl: false,
		fullscreenControl: false,

		gestureHandling: "greedy"
	});

	let MAP_BOUNDS = new google.maps.LatLngBounds();
	MAP_BOUNDS.extend(new google.maps.LatLng(api.map.extendToNorth.lat, api.map.extendToNorth.lng))

	//google.maps.event.addListenerOnce(mapElem, "tilesloaded", () => {
	//	mapElem.setZoom(5.4); // Forces a re-render to sharpen tiles
	//});

	mapElem.setClickableIcons(false); // for default things (country name)

	const TOOLTIP_OFFSET = {x: 6, y: -20};
	const PIN_SCALE_ON_HOVER = 1.2;
	const PIN_SCALE_SELECTED = 1.6;

	let madePins = [];

	let pinsToMake = structuredClone(api.siteInfo);
	// SORT by lat so northernmost drawn first, 
	// dont want pinpoint overlapping a more southern pin bulge
	pinsToMake.sort((a,b) => { return b.lat - a.lat; });

	let toHighlightRandom;
	if (onPinSelect && !popup) toHighlightRandom = api.random.choice(pinsToMake);

	let thisGrades = grades["default"];

	let selected;

	for (let loc of pinsToMake) {
		let thisData;

		for (let v of data || []) {
			if (loc.mId === v.loc) {thisData = v; break;}
		};


		let thisPin = new PinConstruct({
			title: loc.name,
			scale: 0.5,

			borderColor: "#464046",
			glyphColor: "#464046"
		});

		let pinDOMElem = thisPin.element;

		let pinColourBkg = pinDOMElem.querySelector(".RIFvHW-maps-pin-view-background");
		api.dom.setElemGrade(pinColourBkg, thisGrades[loc.mId]);

		madePins.push(thisPin);

		console.log(MAP_BOUNDS, loc);
		if (loc.mId !== 3006) MAP_BOUNDS.extend(new google.maps.LatLng(loc.lat, loc.long));

		let marker = new MarkerConstruct({
			map: mapElem,
			position: {lat: loc["lat"], lng: loc["long"]},
			content: pinDOMElem,
			gmpClickable: true
		});

		marker.addListener("gmp-click", (event, latLng) => {
			if (popup) {
				mapCont.firstChild.remove();
				mapCont.className = "invisible";
			};

			if (selected) {
				setScale(selected, 1);
			};

			if (onPinSelect) {
				selected = pinDOMElem;
				setScale(selected, PIN_SCALE_SELECTED);

				onPinSelect(thisData || loc, pinColourBkg);
			};
		});

		if (toHighlightRandom === loc) marker.click();

		let label;

		// marker.content === pinDOMElem
		// for events, use marker.element (markerDOMElem), bcs cursor: pointer is by marker
		// and pin is svg, box around it where only hovering marker but cursor is pointer.
		marker.element.addEventListener("mouseenter", (event) => {
			label = document.createElement("a");
			label.className = "map-pin-tooltip";
			label.text = loc.clean_name;

			// position: fixed = relative to body
			// position: absolute = relative to first positioned ancestor.
			// tooltip now absolute, first ancestor = mapCont (position: relative; inline)
			let tooltipRelativeTo = mapCont;//.offsetParent;
			tooltipRelativeTo = tooltipRelativeTo.getBoundingClientRect();

			let pos = pinDOMElem.getBoundingClientRect();
			let zoom = mapElem.getZoom();			

			label.style.fontSize = String(zoom / (5.4/1.25)) + "vh";

			let offsetX = (zoom / (5.4 / TOOLTIP_OFFSET.x)) * PIN_SCALE_ON_HOVER;
			let offsetY = (zoom / (5.4 / TOOLTIP_OFFSET.y)) * PIN_SCALE_ON_HOVER;

			// pin worldspace pos - tooltip offset parent worldspace pos = mapspace pin pos
			// mapspace pin pos + offset = mapspace tooltip pos
			label.style.left = String(pos.left - tooltipRelativeTo.left + offsetX) + "px";
			label.style.top = String(pos.top - tooltipRelativeTo.top + offsetY) + "px";

			mapCont.append(label);

			setTimeout(function() { // delay slightly so transition will occur.
				label.style.opacity = "1";
			});

			if (pinDOMElem === selected) return;

			setScale(pinDOMElem, PIN_SCALE_ON_HOVER);
		});

		marker.element.addEventListener("mousedown", (event) => {
			if (!label) return;
			label.remove();
		});

		marker.element.addEventListener("mouseleave", (event) => {
			event.stopPropagation();
			event.preventDefault();
			if (!label) return;

			label.remove();

			if (pinDOMElem === selected) {
				setScale(pinDOMElem, PIN_SCALE_SELECTED);
			} else {
				setScale(pinDOMElem, 1);
			};
		});
	};


	mapElem.fitBounds(MAP_BOUNDS, api.map.boundsPadding);


	google.maps.event.addListener(mapElem, "zoom_changed", () => {
		let zoom = mapElem.getZoom();
		let scale = zoom / (5.4/0.5);

		if (zoom > 7) scale = zoom / (7/0.8)

		for (let marker of madePins) {
			marker.scale = scale;
		};

		for (let label of mapCont.querySelectorAll(".map-pin-tooltip")) {
			label.remove();
		};
	});
}



function initMap(opts) {
	// selector: css selector to find map cont, str
	// popup: whether to hide map once a pin is selected, bool
	// colours: detail about colours {loc: grade}, or "#hex-value"

	Promise.all([
		google.maps.importLibrary("maps"),
		google.maps.importLibrary("marker")
	]).then((values) => {
		let MapConstruct = values[0].Map;
		let MarkerConstruct = values[1].AdvancedMarkerElement;
		let PinConstruct = values[1].PinElement;

		opts["MapConstruct"] = MapConstruct;
		opts["MarkerConstruct"] = MarkerConstruct;
		opts["PinConstruct"] = PinConstruct;

		actualInitMap(opts);
	});
};





function insertSVGByOrg(elemToReplaceOuterHTML, org) {
	let outerHTML;

	if (org === "MO") {
		outerHTML = api.assets.moSVG.outerHTML;
	} else if (org === "BBC") {
		outerHTML = api.assets.bbcSVG.outerHTML;
	} else if (org === "EQUALS") {
		outerHTML = api.assets.equalsSVG.outerHTML;
	} else {
		console.error("What is this org for isnerting svg", org, "for",elemToReplaceOuterHTML);

		return;
	};

	elemToReplaceOuterHTML.outerHTML = outerHTML;
};


function FillSummaryPieGrades(selector, weatherEntries, showLegend) {
	let pieCont = document.querySelector(selector);

	let counts = {};
	for (let entry of weatherEntries) {
		let grade = entry.ga;

		if (!counts[grade]) counts[grade] = 0;
		
		counts[grade] ++;
	};

	let orderedPieSegs = Object.entries(counts).sort( (a, b) => GRADES.indexOf(b[0]) > GRADES.indexOf(a[0]));
	let pieData = [["Grade", "Number of locations"]].concat(orderedPieSegs);
	let colours = orderedPieSegs.map( ([k,v]) => api.colours[k] );

	let width = pieCont.parentElement.getBoundingClientRect().width;

	//if (width < 300) showLegend = false;

	let options = {
		is3D: true,
		colors: colours,
		pieSliceText: "value",
		legend: {position: (!!showLegend) ? "right" : "none"},
		tooltip: {
			isHtml: true,
			ignoreBounds: true,
			text: "percentage"
		},
		chartArea: {
			width: "100%",
			height: "100%"
		},
		backgroundColor: "transparent"
	};

	let gPieData = google.visualization.arrayToDataTable(pieData);
	let chart = new google.visualization.PieChart(pieCont);
	chart.draw(gPieData, options);
};

function FillSummaryTableGrades(table, weatherEntries) {
	let counts = {};
	for (let entry of weatherEntries) {
		let grade = entry.ga;

		if (!counts[grade]) counts[grade] = 0;
		
		counts[grade] ++;
	};

	let percs = {};
	let totalPercs = 0;
	for (let [grade, count] of Object.entries(counts)) {
		let thisPerc = Math.floor((count / weatherEntries.length) * 100);
		percs[grade] = thisPerc;
		totalPercs += thisPerc;
	};

	let percValues = Object.values(percs);
	let maxPercGrade = Object.keys(percs)[percValues.indexOf(Math.max(...percValues))];
	let rem = 100 - totalPercs;
	percs[maxPercGrade] += rem;


	for (let grade of GRADES) {
		let valObj = table.querySelector(`tr:has(td[grade="${grade}"]) td:nth-child(2)`);
		valObj.innerHTML = String(percs[grade] || 0) + "%";
	};
};

function FillSummaryTableConditions(table, orgDetail) {
	function onRowClick(elem) {
		let thisCond = elem.getAttribute("cond");

		if (thisCond === "f") {
			elem = elem.parentElement.querySelector("[cond=\"t\"]");

		} else if (thisCond === "wg" || thisCond === "wd") {
			elem = elem.parentElement.querySelector("[cond=\"ws\"]");
		};

		let alreadyClicked = elem.classList.contains("clicked");
		
		if (alreadyClicked) elem.classList.remove("clicked");
		else elem.classList.add("clicked");
	};

	orgDetail = orgDetail || {r: {}};

	table.innerHTML = "";

	let added = [];

	for (let [k,v] of Object.entries(api.summaryTableKeys)) {
		let name = v[1];
		let unit = v[2]
		let value = orgDetail.r[k];
		let grade = orgDetail.r["g" + k]

		if (value === undefined) continue;

		let valObj = api.assets.conditionTr.cloneNode(true);

		valObj.style.display = "";
		
		valObj.children[0].innerHTML = name + ":";
		valObj.children[1].innerHTML = grade;
		api.dom.setElemGrade(valObj.children[1], grade);
		valObj.children[2].innerHTML = String(value) + " " + unit;

		valObj.setAttribute("cond", k);
		valObj.onclick = () => onRowClick(valObj);

		table.append(valObj);
		added.push(valObj);
	};
};

function getWeekdayFromDateSunday0ToMonday0(dt) {
	return (dt.getUTCDay() + 6) % 7;
};

function indentifierFromDate(dt) {
	return String(dt.getUTCDate()) + "/" + String(dt.getUTCMonth() + 1); // month is zero based
};

function chooseBestGrade(moGrade, bbcGrade, worst) {
	let moScore = api.grades.indexOf(moGrade);
	let bbcScore = api.grades.indexOf(bbcGrade);

	let moBest = moScore > bbcScore;
	let bbcBest = moScore < bbcScore;

	if ((!worst && moBest) || (worst && bbcBest)) {
		return ["MO", moGrade];

	} else if ((!worst && bbcBest) || (worst && moBest)) {
		return ["BBC", bbcGrade];

	} else {
		return ["EQUALS", moGrade];
	};
};

function fillOneGradeDateElem(period, dt, calendarCont, worst, onHover, highlight) {
	let dateElem = api.assets.dateOneGradeTemplate.cloneNode(true);
	let gradeText = dateElem.querySelector("label[grade]");

	let [bestOrg, bestGrade] = api.calc.chooseBestGrade(
		(api.calc.getOrgFromPeriod(period, "MO")).ga,
		(api.calc.getOrgFromPeriod(period, "BBC")).ga,
		worst
	);

	api.dom.insertSVGByOrg(dateElem.querySelector("svg"), bestOrg);
	api.dom.setElemGrade(gradeText, bestGrade);
	dateElem.setAttribute("best", bestOrg);
	

	let dateStr = String(dt.getUTCDate()).padStart(2, "0");
	if (dateStr === "01") {
		dateStr = "1 " + api.datetime.months[dt.getUTCMonth()];
	};

	if (highlight) dateStr += " " + highlight;

	dateElem.querySelector(".datetxt").innerHTML = dateStr;

	calendarCont.append(dateElem);

	if (!onHover) return;
	dateElem.addEventListener("mouseover", () => {
		onHover(dateElem, period, dt, calendarCont, bestOrg, bestGrade);
	});
	dateElem.addEventListener("click", () => {
		onHover(dateElem, period, dt, calendarCont, bestOrg, bestGrade, true);
	});

	//if (highlight) onHover(dateElem, period, dt, calendarCont, bestOrg, bestGrade, true);
};


function fillTwoGradeDateElem(period, dt, calendarCont, highlight) {
	let dateElem = api.assets.dateTwoGradeTemplate.cloneNode(true);

	let mo = api.calc.getOrgFromPeriod(period, "MO").ga;
	let bc = api.calc.getOrgFromPeriod(period, "BBC").ga;

	if (mo) {
		api.dom.setElemGrade(dateElem.querySelector(".mo label[grade]"), mo);
	
	} else {
		dateElem.querySelector(".mo").style.display = "none";
	};

	if (bc) {
		api.dom.setElemGrade(dateElem.querySelector(".bbc label[grade]"), mo);
	
	} else {
		dateElem.querySelector(".bbc").style.display = "none";
	};

	let dateStr = String(dt.getUTCDate()).padStart(2, "0");
	if (dateStr === "01") {
		dateStr = "1 " + api.datetime.months[dt.getUTCMonth()];
	};

	if (highlight) dateStr += " " + highlight;

	dateElem.querySelector(".datetxt").innerHTML = dateStr;

	calendarCont.append(dateElem);
};

function FillCalendar(selector, data, duration, calType, dateOnHover, highlights, twoGradeElem) {
	if (!highlights) highlights = {};

	function pad(startDate, n, calendarCont) {
		for (let i = 0; i < n; i++) {
			let dateElem = api.assets.dateOneGradeTemplate.cloneNode(true);

			let thisDt = new Date(startDate.getTime() + (i * 1000 * 60 * 60 * 24));
			let dateStr = String(thisDt.getUTCDate()).padStart(2, "0");

			let highlight = highlights[api.datetime.indentifierFromDate(thisDt)];

			if (dateStr === "01") dateStr = "1 " + api.datetime.months[thisDt.getUTCMonth()];
			if (highlight) dateStr += " " + highlight;
	
			for (let child of [...dateElem.children]) {
				if (!child.matches(".datetxt")) { child.remove(); continue; };
	
				child.innerHTML = dateStr;
			};
	
			calendarCont.append(dateElem);
		};
	};

	function FillDayHeader(startDate) {
		let header = calendar.querySelector(".day-header");
		let days = [];

		if (calType === "regularWeeks") {
			days = api.datetime.daysMon0;

		} else if (calType === "dynamicWeeksWithGaps") {
			if (!startDate) startDate = new Date((new Date()).getTime() - (duration * 1000 * 60 * 60 * 24));

			let startWeekday = api.datetime.getWeekdayFromDateSunday0ToMonday0(startDate);

			for (let i = 0; i < 7; i++) {
				days.push(api.datetime.daysMon0[(startWeekday + i) % 7]);
			};
		} else if (calType === "dynamicWeeksNoGaps") {
			// iter thru each period, days.push(period.dt.weekday)
		};

		for (let day of days) {
			let newElem = document.createElement("a");
			
			newElem.setAttribute("class", "day");
			newElem.textContent = day;

			header.append(newElem);
		};
	};

	function DefinedPeriods(periodByDate, calendarCont, startDate) {
		if (!startDate) startDate = new Date((new Date()).getTime() - (duration * 1000 * 60 * 60 * 24));

		for (let i = 0; i < duration; i++) {
			let dateNow = new Date(startDate.getTime() + (i * 1000 * 60 * 60 * 24));
			let id = api.datetime.indentifierFromDate(dateNow);
			let period = periodByDate[id]; // do dict incase period doesnt exist
			let highlight = highlights[id];
	
			if (!period) { pad(dateNow, 1, calendarCont); continue; };
	
			
			if (twoGradeElem) { api.dom.fillTwoGradeDateElem(period,dateNow, calendarCont, false); continue; };
			api.dom.fillOneGradeDateElem(period, dateNow, calendarCont, false, dateOnHover, highlight);
		};
	};

	function WithRegularWeeks(paramData, calendarCont) {
		let today = new Date(); // LAST DATE that shows on calendar is YESTERDAY

		let startDate = new Date(today.getTime() - (duration * 1000 * 60 * 60 * 24));
		let startWeekday = api.datetime.getWeekdayFromDateSunday0ToMonday0(startDate);
		let nRows = Math.ceil((startWeekday + duration) / 7);
	
		calendar.style.setProperty("--n-weeks", String(nRows));

		// pad start
		let firstMonday = new Date(startDate.getTime() - (startWeekday * 1000 * 60 * 60 * 24));
		pad(firstMonday, startWeekday, calendarCont);

		// fill normal elems
		DefinedPeriods(paramData, calendarCont, startDate);

		// pad end
		let yesterday = new Date(today.getTime() - (1000 * 60 * 60 * 24));
		let endToPad = 6 - api.datetime.getWeekdayFromDateSunday0ToMonday0(yesterday);
		pad(today, endToPad, calendarCont); // start is INCLUSIVE, so use today as param.
	};


	let calendar = document.querySelector(selector);
	calendar.innerHTML = api.assets.calendarTemplate.innerHTML;

	let calendarCont = calendar.querySelector(".calendar-cont");

	let paramData = data;
	let startDate;

	if (calType === "regularWeeks" || calType === "dynamicWeeksWithGaps") {
		paramData = {};
		startDate = new Date(data[0].ft);

		for (let period of data) {
			let dt = new Date(period.ft);
			
			paramData[api.datetime.indentifierFromDate(dt)] = period;
		};
	};

	FillDayHeader(startDate);

	if (calType === "regularWeeks") WithRegularWeeks(paramData, calendarCont);
	else if (calType === "dynamicWeeksWithGaps") DefinedPeriods(paramData, calendarCont, startDate);
};


function setElemGrade(elem, grade) {
	grade = grade || "";

	if (grade.startsWith("#")) grade = COLOUR_TO_GRADE[grade];

	elem.setAttribute("grade", grade);

	grade = grade.replace("+", "<sup>+</sup>");
	if (elem.tagName && api.textTags.includes(elem.tagName.toUpperCase())) elem.innerHTML = grade;
};


function averageOfGrades(data, returnIntScore) {
	let total = data.reduce((acc, v) => acc + GRADES.indexOf(v), 0);
	let averageIndex = total / data.length;

	if (returnIntScore === true) return averageIndex;

	let closestIndex = Math.round(averageIndex);
	
	v = GRADES[closestIndex]
	//if (v === "X") v = "A"

	return v;
};

function hyperbolicAvgGrades(data) { // gets value furthest from median available grade (C)
	let indexes = data.map((v) => GRADES.indexOf(v));
	let diffFromMid = indexes.map((v) => Math.abs((GRADES.length / 2) - v));

	let index = diffFromMid.indexOf(Math.max(...diffFromMid));
	let value = indexes[index]; // === gradeI
	let grade = GRADES[value]; 

	return grade;
};

function getGradeByLocArr(moData, bbcData) {
	let gradesByLoc = [];

	for (let mId of api.locIds) {
		let mGrade = moData.filter( v => v.i === mId );
		let bGrade = bbcData.filter( v => v.i === mId );

		let o = {loc: mId};

		if (mGrade && mGrade.length > 0) {
			o.mo = mGrade[0];
		};

		if (bGrade && bGrade.length > 0) {
			o.bbc = bGrade[0];
		};

		gradesByLoc.push(o);
	};

	return gradesByLoc;
};

function getOrgFromPeriod(period, org) {
	if (org == "MO") return period.M1 || period.M3 || {data: []};
	else if (org == "BBC") return period.B1 || period.BD || {data: []};
};


function getBestOrgFromPeriods(periods) {
	let mo = [];
	let bc = [];

	for (let period of periods) {
		let thisMo = [];

		if (period.M1) thisMo.push(GRADES.indexOf(period.M1.ga));
		if (period.M3) thisMo.push(GRADES.indexOf(period.M3.ga));

		let bestMo = Math.max(thisMo);
		if (bestMo) thisMo = GRADES[thisMo];

		let thisBc = [];
		if (period.B1) thisBc.push(GRADES.indexOf(period.B1.ga));
		if (period.BD) thisBc.push(GRADES.indexOf(period.BD.ga));

		let bestBc = Math.max(thisBc);
		if (bestBc) thisBc = GRADES[thisBc];

		if (thisMo) mo.push(thisMo);
		if (thisBc) bc.push(thisBc);
	};

	let moAvg = api.calc.averageOfGrades(mo, true);
	let bcAvg = api.calc.averageOfGrades(bc, true);

	if (moAvg > bcAvg) return "MO";
	else if (bcAvg > moAvg) return "BBC";
	else return "EQUALS"
};

function getAvgObs(obss) {
	let sums = {};
	for (let k of Object.keys(obss[0])) sums[k] = [];

	for (let obs of Object.values(obss)) {
		for (let [k,v] of Object.entries(obs)) {
			if (typeof(v) !== "number") {
				if (k !== "pr") continue;

				v = 0;
			};

			sums[k].push(v);
		};
	};

	let final = {};

	for (let [k,v] of Object.entries(sums)) {
		let decimals = 1;
		if (k === "w") decimals = 0;

		final[k] = Math.round(api.calc.sum(v) / v.length * (10**decimals)) / (10**decimals);
	};

	return final;
};

function sum(arr) {
	return arr.reduce((acc, thisv) => acc + thisv, 0);
};


function getMapGrades(data, mode) {
	// mode = avg (simple)
	// 		hyp (hyperbolic, most extreme away from middle of grades)

	let gradesByToggle = {
		default: {},
		mo: {},
		bbc: {}
	}

	for (let loc of data) {
		let grades = [];

		if (loc.mo) grades.push(loc.mo.ga);
		if (loc.bbc) grades.push(loc.bbc.ga);

		let grade;

		if (mode === "avg") grade = api.calc.averageOfGrades(grades);
		else if (mode === "hyp") grade = api.calc.hyperbolicAvgGrades(grades);

		gradesByToggle.default[loc.loc] = grade;
		if (loc.mo) gradesByToggle.mo[loc.loc] = loc.mo.ga;
		if (loc.bbc) gradesByToggle.bbc[loc.loc] = loc.bbc.ga;
	};

	return gradesByToggle;
};

function randomInt(lowerInc, upperInc) {
	return lowerInc + Math.round(Math.random() * (upperInc - lowerInc));
}

function randomChoice(list) {
	return list[api.random.int(0, list.length - 1)]
};

function stringTitle(str) {
	return str.replace(/\b(\w)/g, (match, p1) => p1.toUpperCase());
};


function _setContentBody(innerHTML, historyDetail) {
	let content = document.querySelector("#content");

	let tempElem = document.createElement("div");
	tempElem.innerHTML = innerHTML.replace("\t","");

	let contentElem = tempElem.querySelector("div");

	content.scrollTo({
		top: 0,
		left: 0,
		behavior: "instant"
	});

	let currentContent = content.querySelector(".content-elem");
	if (currentContent) currentContent.remove(); // removes current WITHOUT removing footer


	content.insertBefore(contentElem, content.firstElementChild);
	tempElem.remove();

	let scriptSrc = contentElem.getAttribute("scriptsrc");
	if (scriptSrc) {
		let script = document.createElement("script");
		script.setAttribute("src", scriptSrc);
		document.head.append(script);

		contentElem.removeAttribute("scriptsrc");
	};

	let popupMap = document.querySelector("#popup-map-cont");
	popupMap.className = "invisible";
	popupMap.innerHTML = "";



	if (!historyDetail) return;

	let title = api.navigation.pageTitles[historyDetail.url];
	document.title = title + " - " + api.navigation.masterTitle;

	// state is a custom serialisable object that cna store anything, to be used in popstate events.
	if (historyDetail.pushState === true) {
		window.history.pushState({ 
			"_contentInnerHTML": innerHTML,
			"_relHref": historyDetail.url + historyDetail.searchText
		}, "", historyDetail.url + historyDetail.searchText);
	};
};

function innerNavigateTo(relativeHref) {
	let params;
	let searchText = "";

	if (typeof(relativeHref) === "object") {
		params = relativeHref.searchParams;
		searchText = relativeHref.search;

		relativeHref = relativeHref.pathname;
	};

	let cdnURI = api.navigation.cdnURI[relativeHref];

	fetch(cdnURI).then(

		async function(response) {
			let innerHTML = await response.text();

			api.dom._setContentBody(innerHTML, {url: relativeHref, params: params, searchText: searchText, pushState: true});
		}, 

		function(err) {
			console.error("promise rejection grabbing content body at uri", cdnURI, err);

			setTimeout(() => innerNavigateTo(relativeHref), 1000);
		}

	);
};

function setLocCardName(locName) {
	document.querySelector("#loc-card label").textContent = locName;
};





function initApi() {
	let api = {
		dom: {
			innerNavigateTo: innerNavigateTo,
			_setContentBody: _setContentBody,
			FillSummaryTableGrades: FillSummaryTableGrades,
			FillSummaryTableConditions: FillSummaryTableConditions,
			FillCalendar: FillCalendar,
			fillOneGradeDateElem: fillOneGradeDateElem,
			fillTwoGradeDateElem: fillTwoGradeDateElem,
			setElemGrade: setElemGrade,
			getMapGrades: getMapGrades,
			initMap: initMap,
			insertSVGByOrg: insertSVGByOrg,
			setLocCardName: setLocCardName,
			FillSummaryPieGrades: FillSummaryPieGrades
		},
		api: {
			getContentBody: null,
			getApiWeekOfDailySummaries: getApiWeekOfDailySummaries,
			getApiMonthOfDailySummaries: getApiMonthOfDailySummaries,
			getApiWeekOfDailyResultsOfFuture: getApiWeekOfDailyResultsOfFuture,
			fetchSiteInfo: fetchSiteInfo,
			getApiFcstsOfDay: getApiFcstsOfDay,
			getApiObsofDay: getApiObsofDay
		},
		calc: {
			averageOfGrades: averageOfGrades,
			hyperbolicAvgGrades: hyperbolicAvgGrades,
			chooseBestGrade: chooseBestGrade,
			getGradeByLocArr: getGradeByLocArr,
			getOrgFromPeriod: getOrgFromPeriod,
			getBestOrgFromPeriods: getBestOrgFromPeriods,
			getAvgObs: getAvgObs,
			sum: sum
		},
		random: {
			int: randomInt,
			choice: randomChoice
		},
		str: {
			title: stringTitle
		},
		datetime: {
			getWeekdayFromDateSunday0ToMonday0: getWeekdayFromDateSunday0ToMonday0,
			indentifierFromDate: indentifierFromDate,
			daysMon0: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
			months: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
		},
		assets: {
			moSVG: document.querySelector("template#mo-svg").content.children[0],
			bbcSVG: document.querySelector("template#bbc-svg").content.children[0],
			equalsSVG: document.querySelector("template#equals-svg").content.children[0],
			dateOneGradeTemplate: document.querySelector("template#calendar-date-onegrade-square").content.children[0],
			dateTwoGradeTemplate: document.querySelector("template#calendar-date-twograde-square").content.children[0],
			calendarTemplate: document.querySelector("template#calendar").content.children[0],
			conditionTr: document.querySelector("template#condition-tr").content.children[0],
			fcstObsPeriodTemplate: document.querySelector("template#fcstvsobs").content.children[0],
			fcstObsPeriodKey: document.querySelector("template#fcstvsobskey").content.children[0]
		},
		map: {
			id: "9e1930bb750ee894",
			defaultColour: "#0ab6ff", //"#02006b",
			borderColour: "#464046",
			centre: {lat: 55.81511846508342, lng: -3.7059529463830354},
			extendToNorth: {lat: 58.637216164602556, lng: -3.0689814701912654},
			boundsPadding: {top: 15, bottom: 5, left: 30, right: 30}
		},
		navigation: {
			masterTitle: "Cloudy?",
			pageTitles: {
				"/": "Home",
				"/local": "Local",
				"/changes": "Changes"
			},
			cdnURI: {
				"/": "https://weatherstatic.gtweb.dev/doc/home.html",
				"/local": "https://weatherstatic.gtweb.dev/doc/local.html",
				"/changes": "https://weatherstatic.gtweb.dev/doc/changes.html"
			}
		},
		config: {
			monthNDays: 30
		},
		grades: GRADES,
		siteInfo: [],
		locIds: [],
		siteInfoDict: {},
		textTags: [
			'A', 'LABEL', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
			'P', 'SPAN', 'B', 'I', 'U', 'STRONG', 'EM',
			'SMALL', 'MARK', 'DEL', 'INS', 'SUB', 'SUP',
			'Q', 'BLOCKQUOTE', 'CITE', 'TIME', 'CODE', 'PRE', "TD"
		],
		units: {
			temp: "\u00B0C",
			score: "%",
			speed: "km/h",
			direction: "\u00B0",
			precip: "mm"
		},
		colours: {
			"A+": "#FF41D8",
			"A": "#2EC918",
			"B": "#ffb600",
			"C": "#FF5400",
			"D": "#C40000",
			"F": "#000000"
		},
		descriptions: {
			PIE_CHART_GRADES: "The pie charts show the the number of weather stations which received each grade, per forecaster.",
			SUMMARY: "Difference between forecast and actual for yesterday's weather"
		},
		nightWTsMap: {2: 0, 3: 1},
		transferKeys: {},
		summaryTableKeys: {}
	};

	window.api = api;

	api.transferKeys = {
		"t": ["d_scr_temp", "Temperature", api.units.temp],
		"f": ["d_feels_like", "Feels Like", api.units.temp],
		"w": ["s_wt", "Weather Type", api.units.score],
		"ws": ["d_wind_s", "Wind Speed", api.units.speed],
		"wd": ["d_wind_d", "Wind Direction", api.units.direction],
		"wg": ["d_wind_g", "Wind Gust", api.units.speed],
		"pt": ["s_p_timing", "Precip Timing", api.units.score],
		"pr": ["s_p_rate", "Precip Rate", api.units.score],
		"pi": ["s_p_type", "Precip Intensity", api.units.score],
		"pc": ["s_p_conf", "Precip Confidence", api.units.score],
		"po": ["s_p_ovrl", "Precipitation", api.units.score]
	},

	api.summaryTableKeys = {
		"t": api.transferKeys.t,
		"f": api.transferKeys.f,
		"p": api.transferKeys.po,
		"ws": api.transferKeys.ws,
		"wg": api.transferKeys.wg,
		"wd": api.transferKeys.wd,
		"w": api.transferKeys.w
	}


	fetchSiteInfo(true).then((json) => {
		window.api.siteInfo = Array.from(Object.values(json));
		window.api.locIds = window.api.siteInfo.map( v => Number(v.mId) );
		window.api.siteInfoDict = json;
	}); // TODO: RETRY THIS!
};












function OnLoad() {
	console.log("onload", window.location.pathname);

	initApi();

	innerNavigateTo(new URL(window.location.href));

	for (let elem of document.querySelectorAll("#navbar > a[href]")) {

		elem.addEventListener("click", function(e) {
			e.preventDefault();
			e.stopImmediatePropagation();

			innerNavigateTo(elem.getAttribute("href"));
		});

	};

	window.addEventListener("popstate", function(e) {
		if (!e.state) return;

		api.dom._setContentBody(e.state._contentInnerHTML, {
			url: e.state._relHref,
			pushState: false
		});

	});

	document.querySelector("#loc-card").addEventListener("click", function(e) {
		try {
			api.dom.initMap({
				data: api.siteInfo,
				selector: "#popup-map-cont",
				popup: true,
				onPinSelect: (data, pinElem) => {
					let current = new URL(window.location.href);
					current.searchParams.set("locId", data.mId);
					console.log(data, current);

					innerNavigateTo(current);
					setLocCardName(api.siteInfoDict[data.mId].clean_name);
				}
			});
		} catch(err) {
			console.error("couldn't init map", err);
		};		
	});
};

console.log(document.readyState);

if (document.readyState !== "complete") window.addEventListener("load", OnLoad);
else OnLoad();