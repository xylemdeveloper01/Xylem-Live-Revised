
function getImageWidthHeightOfPanel(imgNaturalWidth, imgNaturalHeight, panelWidth, panelHeight){
  var mf = panelWidth/imgNaturalWidth
  if (imgNaturalHeight*mf > panelHeight){
    mf = panelHeight/imgNaturalHeight
  }
  var width = imgNaturalWidth*mf;
  var height = imgNaturalHeight*mf;

  var img_space_hori =  panelWidth - width
  var img_space_vert =  panelHeight - height

  return [width, height, img_space_hori, img_space_vert]
}


function exportPdf(table1Id, table2Id) {
  var pdf = new jsPDF('l', 'mm', 'a4');

  var table1 = document.getElementById(table1Id);
  var table2 = document.getElementById(table2Id);

  var xylem_logo = new Image();
  xylem_logo.src = "{% static 'assets/images/xylem-logo.png' %}";

  var company_logo = new Image();
  company_logo.src = "{% static 'assets/images/ZF_Rane.png' %}";

  var tool_image = new Image();
  tool_image.src = $('#tool_image').attr('src');

  marginTop = 5
  marginBottom = 5
  marginLeft = 5
  marginRight = 5
  additionalSpace = 5
  headerHeight = 10
  footerHeight = 5
  headerFontSize = 20
  headerFontColor = 20
  footerFontSize = 10
  footerpageNumFontSize = 5
  headerFooterColor = [52, 58, 64] // '#343A40'
  headerFooterLineLogoGap = 2
  headerFooterLineThickness = 0.4
  dividingLineColor = [136, 136, 136] // '#888888'
  dividingLineThickness = 0.3

  pdfWidth = pdf.internal.pageSize.width
  pdfHeight = pdf.internal.pageSize.height

  pdfHeaderText = "Tool History Card" //Should be less length
  pdfFooterText = "Xylem - An Inhouse Development" //Should be less length

  full_size_table = {
    html: null,
    startY: 0,
    theme: null,
    styles: {minCellHeight: 10},
    tableWidth: pdfWidth - marginLeft - marginRight,
    columnStyles: {},
    margin: {
      top: marginTop + headerHeight + additionalSpace,
      bottom: marginBottom + footerHeight + additionalSpace,
      left: marginLeft,
      right: marginRight
    },
    headStyles : null,
    didParseCell: null,
    rowPageBreak: "avoid",
  }
  half_size_table = structuredClone(full_size_table)
  half_size_table.tableWidth = (pdfWidth - marginLeft - marginLeft - additionalSpace)/ 2


  function CustomHeadStyleBlue(data) {
    if (data.cell.raw.tagName === 'TH') {              
      data.cell.styles.fillColor = [45, 131, 188]; // blue background
      data.cell.styles.textColor = [255, 255, 255]; // White text
      data.cell.styles.fontStyle = 'bold';                              
      data.cell.styles.lineWidth = 0.3;                              
      data.cell.styles.lineColor = [221, 221, 221];          
      
      // add extra custom styles below
    }
  }


  function CustomHeadStyleGreen(data) {
    if (data.cell.raw.tagName === 'TH') {              
      data.cell.styles.fillColor = [44, 184, 149]; // blue background
      data.cell.styles.textColor = [255, 255, 255]; // White text
      data.cell.styles.fontStyle = 'bold';                              
      data.cell.styles.lineWidth = 0.3;                              
      data.cell.styles.lineColor = [221, 221, 221];      
      
      // add extra custom styles below
    }
  }


  function generate_pdf(){
    X = marginLeft
    Y = marginTop + headerHeight + additionalSpace

    // table 1
    tempTableParam = structuredClone(half_size_table)
    tempTableParam.html = table1
    tempTableParam.startY = Y
    tempTableParam.theme = "striped"
    pdf.autoTable(tempTableParam)

    // tool image
    X = X + tempTableParam.tableWidth + additionalSpace
    var [img_w, img_h, hori_space, verti_space] = getImageWidthHeightOfPanel(tool_image.naturalWidth, tool_image.naturalHeight, pdfWidth - X - marginRight, pdf.autoTable.previous.finalY - Y)
    pdf.addImage(tool_image, 'PNG', X + (hori_space / 2), Y + (verti_space / 2), img_w, img_h)

    // line below table 1 & tool image
    X = marginLeft
    Y = pdf.autoTable.previous.finalY + additionalSpace
    pdf.setDrawColor(dividingLineColor[0], dividingLineColor[1], dividingLineColor[2])
    pdf.setLineWidth(dividingLineThickness)
    pdf.line(X, Y, pdfWidth - X, Y)

    // table 2
    Y = Y + dividingLineThickness + additionalSpace
    tempTableParam = structuredClone(full_size_table)
    tempTableParam.html = table2
    tempTableParam.startY = Y
    tempTableParam.theme = "striped"
    tempTableParam.columnStyles = {2: {cellWidth: 73}}
    pdf.autoTable(tempTableParam)

    const totalPages = pdf.internal.getNumberOfPages()
    for (let i = 1; i <= totalPages; i++) {
      pdf.setPage(i)
      X = marginLeft
      Y = marginTop
      headerPanelHeight = headerHeight - headerFooterLineLogoGap - headerFooterLineThickness
      footerPanelHeight = footerHeight - headerFooterLineLogoGap - headerFooterLineThickness

      // xylem logo
      var [img_w, img_h, hori_space, verti_space] = getImageWidthHeightOfPanel(xylem_logo.naturalWidth, xylem_logo.naturalHeight, pdfWidth, headerPanelHeight)
      pdf.addImage(xylem_logo, 'PNG', X, Y, img_w, img_h)
      
      // company logo
      var [img_w, img_h, hori_space, verti_space] = getImageWidthHeightOfPanel(company_logo.naturalWidth, company_logo.naturalHeight, pdfWidth, headerPanelHeight)
      pdf.addImage(company_logo, 'PNG', pdfWidth - img_w - marginRight, Y, img_w, img_h)

      // header text
      Y = Y + headerPanelHeight
      pdf.setTextColor(headerFooterColor[0], headerFooterColor[1], headerFooterColor[2])
      pdf.setFontSize(headerFontSize)
      pdf.setFontStyle('bold')
      pdf.text(pdfHeaderText, pdfWidth/2, Y, {align: 'center'})

      // line below header
      Y = Y + headerFooterLineLogoGap
      pdf.setDrawColor(headerFooterColor[0], headerFooterColor[1], headerFooterColor[2])
      pdf.setLineWidth(headerFooterLineThickness)
      pdf.line(X, Y, pdfWidth - X, Y)

      // adding rectangle to hide if any overflow occured inside footer
      space_height = footerHeight + headerFooterLineLogoGap + marginBottom
      Y = pdfHeight - space_height
      pdf.setFillColor(255, 255, 255)
      pdf.rect(0, Y, pdfWidth, space_height, "F")

      // line above footer
      Y = Y + headerFooterLineLogoGap
      pdf.setDrawColor(headerFooterColor[0], headerFooterColor[1], headerFooterColor[2])
      pdf.setLineWidth(headerFooterLineThickness)
      pdf.line(X, Y, pdfWidth - X, Y)

      // footer text
      Y = Y + footerHeight
      pdf.setTextColor(headerFooterColor[0], headerFooterColor[1], headerFooterColor[2])
      pdf.setFontSize(footerFontSize)
      pdf.setFontStyle('bold')
      pdf.text(pdfFooterText, pdfWidth / 2, Y, {align: 'center'})

      // page number
      pdf.setFontSize(footerpageNumFontSize)
      pdf.text(`Page ${i} of ${totalPages}`, pdfWidth - marginRight, Y, {align: 'right'})
    }

    var today = new Date();
    const offset = today.getTimezoneOffset()
    today = new Date(today.getTime() - (offset * 60 * 1000))

    // Save the PDF with a specified filename
    pdf.save(`xylem_a004_tms_tool_history_card_${today.toISOString().split('.')[0]}.pdf`)
  }

  let loadedImages = 0
  images = [xylem_logo, company_logo]
  images.forEach(function(image) {
    if (image.complete) {
      loadedImages++;
      if (loadedImages === images.length){
        generate_pdf()
      }
    } else {
      image.onload = function(){
        loadedImages++;
        if (loadedImages === images.length){
          generate_pdf()
        }
      }
    }
  })
}