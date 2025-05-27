//const GRADES = {"A+": 1, "A": 2, "B": 3, "C": 4, "D": 5, "F": 6};
const GRADES = ["F", "D", "D+", "C", "C+", "B", "B+", "A", "X", "A+"];
const REAL_GRADES = ["F", "D", "C", "B", "A", "A+"];
const GRADE_COLOURS = {"A+": "#FF41D8", "A": "#2EC918", "B": "#23C5D5", "C": "#FF5400", "D": "#C40000", "F": "#000000"}


async function getApiWeekOfDailySummaries() {
	let response = await fetch("/api/results/daily?period=7");

	return (await response.json());
};

async function getApiMonthOfDailySummaries() {
	let response = await fetch(`/api/results/daily?period=${api.config.monthNDays}`);

	return (await response.json());
};

async function fetchSiteInfo(isDict) {
	isDict = Boolean(isDict);

	let response = await fetch(`/api/site-info?dict=${isDict}`);

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








async function initMap({selector, popup, colours, onPinSelect, data}={}) {
	function setScale(pin, newScale) {
		let currentTransform = pin.style.transform || "";
		pin.style.transform = currentTransform.replace(/scale\([\d\.]+\)/g, "") + `scale(${newScale})`;
	};

	// selector: css selector to find map cont, str
	// popup: whether to hide map once a pin is selected, bool
	// colours: detail about colours {loc: grade}, or "#hex-value"

	const {Map} = await google.maps.importLibrary("maps");
	const {AdvancedMarkerElement, PinElement} = await google.maps.importLibrary("marker");

	const mapCont = document.querySelector(selector);
	mapCont.className = mapCont.className.replace("invisible","");

	let mapElem = new Map(mapCont, {
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

	google.maps.event.addListenerOnce(mapElem, "tilesloaded", () => {
		mapElem.setZoom(5.4); // Forces a re-render to sharpen tiles
	});

	mapElem.setClickableIcons(false); // for default things (country name)

	const TOOLTIP_OFFSET = {x: 6, y: -20};
	const PIN_SCALE_ON_HOVER = 1.2;
	const PIN_SCALE_SELECTED = 1.6;

	let madePins = [];

	let pinsToMake = structuredClone(api.siteInfo);
	// SORT by lat so northernmost drawn first, 
	// dont want pinpoint overlapping a more southern pin bulge
	pinsToMake.sort((a,b) => {return b.lat - a.lat;});

	let toHighlightRandom;
	if (onPinSelect) toHighlightRandom = api.random.choice(pinsToMake);

	let selected;

	for (let loc of pinsToMake) {
		let colour = colours[loc.mId] || api.map.defaultColour;
		let thisData;

		if (data) {
			for (let v of data) {
				if (loc.mId === v.loc) {thisData = v; break;}
			};
		};

		let thisPin = new PinElement({
			title: loc.name,
			scale: 0.5,

			background: colour,
			borderColor: "#464046",
			glyphColor: "#464046"
		});

		let pinDOMElem = thisPin.element;

		madePins.push(thisPin);

		let marker = new AdvancedMarkerElement({
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

				onPinSelect(thisData);
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

			//if (pinDOMElem === selected) return;

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

			let currentTransform = pinDOMElem.style.transform || "";

			if (pinDOMElem === selected) {
				setScale(pinDOMElem, PIN_SCALE_SELECTED);
			} else {
				setScale(pinDOMElem, 1);
			};
		});
	};

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


function FillSummaryTableGrades(table, gradeList) {
	let counts = {};
	for (let grade of gradeList) {
		if (!counts[grade]) counts[grade] = 0;
		
		counts[grade] ++;
	};

	let percs = {};
	let totalPercs = 0;
	for (let [grade, count] of Object.entries(counts)) {
		let thisPerc = Math.floor((count / gradeList.length) * 100);
		percs[grade] = thisPerc;
		totalPercs += thisPerc;
	};

	let percValues = Object.values(percs);
	let maxPercGrade = Object.keys(percs)[percValues.indexOf(Math.max(...percValues))];
	let rem = 100 - totalPercs;

	console.log("REMO OF", rem, "GOING TO GRADE", maxPercGrade);
	percs[maxPercGrade] += rem;


	for (let grade of REAL_GRADES) {
		let valObj = table.querySelector(`tr:has(td[grade="${grade}"]) td:nth-child(2)`);
		valObj.innerHTML = String(percs[grade] || 0) + "%";
	};
};

function FillSummaryTableConditions(table, gradeDetail) {
	let rows = table.querySelectorAll(`tr`);

	let i = 0;
	for (let [k,v] of Object.entries(gradeDetail)) {
		let valObj = rows[i];
		
		valObj.children[0].innerHTML = api.str.title(k) + ":";
		valObj.children[1].innerHTML = v.grade;
		api.dom.setElemGrade(valObj.children[1],v.grade);
		valObj.children[2].innerHTML = String(v.perc) + "%";
		i ++;
	};
};

function getWeekdayFromDateSunday0ToMonday0(dt) {
	return (dt.getUTCDay() + 6) % 7;
};

function indentifierFromDate(dt) {
	return String(dt.getUTCDate()) + "/" + String(dt.getUTCMonth())
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

function fillOneGradeDateElem(dateElem, period, dt, calendarCont, worst, onHover) {
	let gradeText = dateElem.querySelector("label[grade]");

	let [bestOrg, bestGrade] = api.calc.chooseBestGrade(period.nationwideMO, period.nationwideBBC, worst);
	api.dom.insertSVGByOrg(dateElem.querySelector("svg"), bestOrg);
	api.dom.setElemGrade(gradeText, bestGrade);
	dateElem.setAttribute("best", bestOrg);
	

	let dateStr = String(dt.getUTCDate()).padStart(2, "0");
	if (dateStr === "01") {
		dateStr = "1 " + api.datetime.months[dt.getUTCMonth()];
	};

	dateElem.querySelector(".datetxt").textContent = dateStr;

	calendarCont.append(dateElem);

	if (!onHover) return;
	dateElem.addEventListener("mouseover", () => {
		console.log("HELLLLLO");
		onHover(dateElem, period, dt, calendarCont, bestOrg, bestGrade);
	});
};

function FillCalendar(selector, data, duration, calType, dateOnHover) {
	function pad(startDate, n, calendarCont) {
		for (let i = 0; i < n; i++) {
			let dateElem = api.assets.dateOneGradeTemplate.cloneNode(true);
	
			for (let child of [...dateElem.children]) {
				if (!child.matches(".datetxt")) { child.remove(); continue; };
	
				let thisDt = new Date(startDate.getTime() + (i * 1000 * 60 * 60 * 24));
				let dateStr = String(thisDt.getUTCDate()).padStart(2, "0");
	
				if (dateStr === "01") dateStr = "1 " + api.datetime.months[thisDt.getUTCMonth()];
				child.textContent = dateStr;
			};
	
			calendarCont.append(dateElem);
		};
	};

	function FillDayHeader() {
		let header = calendar.querySelector(".day-header");
		let days = [];

		if (calType === "regularWeeks") {
			days = api.datetime.daysMon0;

		} else if (calType === "dynamicWeeksWithGaps") {
			let startDate = new Date((new Date()).getTime() - (duration * 1000 * 60 * 60 * 24));
			let startWeekday = api.datetime.getWeekdayFromDateSunday0ToMonday0(startDate);

			for (let i = 0; i < 7; i++) {
				days.push(api.datetime.daysMon0[(startWeekday + i) % 6]);
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

		console.log(startDate);
		for (let i = 0; i < duration; i++) {
			let dateNow = new Date(startDate.getTime() + (i * 1000 * 60 * 60 * 24));
			let period = periodByDate[api.datetime.indentifierFromDate(dateNow)]; // do dict incase period doesnt exist
	
			if (!period) { pad(dateNow, 1, calendarCont); continue; };
	
			let dateElem = api.assets.dateOneGradeTemplate.cloneNode(true);
			api.dom.fillOneGradeDateElem(dateElem, period, dateNow, calendarCont, false, dateOnHover);
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

	FillDayHeader();

	let paramData = data;

	if (calType === "regularWeeks" || calType === "dynamicWeeksWithGaps") {
		paramData = {};

		for (let period of data) {
			let dt = new Date(period.date * 1000); // Date() takes milliseconds, api = seconds.
			paramData[api.datetime.indentifierFromDate(dt)] = period;
		};
	};

	if (calType === "regularWeeks") WithRegularWeeks(paramData, calendarCont);
	else if (calType === "dynamicWeeksWithGaps") DefinedPeriods(paramData, calendarCont);
}


function setElemGrade(elem, grade) {
	elem.setAttribute("grade", grade);

	grade = grade.replace("+", "<sup>+</sup>");
	elem.innerHTML = grade;
};


function averageOfGrades(data, returnIntScore) {
	let total = data.reduce((acc, v) => acc + REAL_GRADES.indexOf(v), 0);
	let averageIndex = total / data.length;

	if (returnIntScore === true) return averageIndex;

	let closestIndex = Math.round(averageIndex);
	
	v = REAL_GRADES[closestIndex]
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


function getMapColours(data, mode) {
	// mode = avg (simple)
	// 		hyp (hyperbolic, most extreme away from middle of grades)

	let colours = {};

	for (let loc of data) {
		let grades = [loc.moGrade, loc.bbcGrade];
		let grade;

		if (mode === "avg") {
			grade = api.calc.averageOfGrades(grades);
		} else if (mode === "hyp") {
			grade = loc.hypAvg;
		};

		colours[loc.loc] = GRADE_COLOURS[grade];
	};

	console.log(colours);

	return colours;
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

	let currentContent = content.querySelector(".content-elem");
	if (currentContent) currentContent.remove(); // removes current WITHOUT removing footer

	content.scrollTo({
		top: 0,
		left: 0,
		behavior: "instant"
	});

	content.insertBefore(contentElem, content.firstElementChild);
	tempElem.remove();

	let scriptSrc = contentElem.getAttribute("scriptsrc");
	if (scriptSrc) {
		let script = document.createElement("script");
		script.setAttribute("src", scriptSrc);
		document.head.append(script);

		contentElem.removeAttribute("scriptsrc");
	};

	if (!historyDetail) return;

	let title = api.navigation.pageTitles[historyDetail.url];
	document.title = title + " - " + api.navigation.masterTitle;

	// state is a custom serialisable object that cna store anything, to be used in popstate events.
	if (historyDetail.pushState === true) {
		window.history.pushState({ 
			"_contentInnerHTML": innerHTML,
			"_relHref": historyDetail.url
		}, "", historyDetail.url);
	};
};

function innerNavigateTo(relativeHref) {
	let cdnURI = api.navigation.cdnURI[relativeHref];

	fetch(cdnURI).then(

		async function(response) {
			let innerHTML = await response.text();

			api.dom._setContentBody(innerHTML, {url: relativeHref, pushState: true});
		}, 

		function(err) {
			console.error("promise rejection grabbing content body at uri", cdnURI, err);

			setTimeout(() => innerNavigateTo(relativeHref), 1000);
		}

	);
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
			setElemGrade: setElemGrade,
			getMapColours: getMapColours,
			initMap: initMap,
			insertSVGByOrg: insertSVGByOrg
		},
		api: {
			getContentBody: null,
			getApiWeekOfDailySummaries: getApiWeekOfDailySummaries,
			getApiMonthOfDailySummaries: getApiMonthOfDailySummaries,
			fetchSiteInfo: fetchSiteInfo
		},
		calc: {
			averageOfGrades: averageOfGrades,
			hyperbolicAvgGrades: hyperbolicAvgGrades,
			chooseBestGrade: chooseBestGrade
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
			calendarTemplate: document.querySelector("template#calendar").content.children[0]
		},
		map: {
			id: "9e1930bb750ee894",
			defaultColour: "#0ab6ff", //"#02006b",
			borderColour: "#464046",
			centre: {lat: 55.81511846508342, lng: -3.7059529463830354}
		},
		navigation: {
			masterTitle: "Cloudy?",
			pageTitles: {
				"/": "Home",
				"/local": "Local",
				"/changes": "Changes"
			},
			cdnURI: {
				"/": "static/doc/home.html",
				"/local": "static/doc/local.html",
				"/changes": "static/doc/changes.html"
			}
		},
		config: {
			monthNDays: 30
		},
		grades: REAL_GRADES,
		
		siteInfo: [],
		siteInfoDict: {}
	};

	window.api = api;

	fetchSiteInfo(false).then((json) => {
		window.api.siteInfo = json;
	}); // TODO: RETRY THIS!

	fetchSiteInfo(true).then((json) => {
		window.api.siteInfoDict = json;
	}); // TODO: RETRY THIS!
};












function OnLoad() {
	console.log("onload", window.location.pathname);

	initApi();

	innerNavigateTo(window.location.pathname);

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
};

console.log(document.readyState);

if (document.readyState !== "complete") window.addEventListener("load", OnLoad);
else OnLoad();