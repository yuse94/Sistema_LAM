# LIBRARIES
from shutil import copyfile
from time import strftime
from arrow import utcnow
from reportlab.platypus import PageBreak
from reportlab.platypus import Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.colors import black, whitesmoke, cornflowerblue, lightsteelblue
from reportlab.pdfgen import canvas
from reportlab.lib import utils


class PageNumbering(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """
        Add page information to each page (page x of y)
        """

        pages_number = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(pages_number)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.drawRightString(204 * mm, 15 * mm + (5 * mm), f'{self._pageNumber}/{page_count}')


class HeaderAndFooter:

    def __init__(self, patient_name):
        self.patient_name = patient_name

    def print_header_and_footer(self, canvas_header, file_pdf):
        """
        Save the state of our canvas so that we can take advantage of it

        :param canvas_header:
        :param file_pdf:
        :return:
        """

        canvas_header.saveState()
        style = getSampleStyleSheet()

        alignment = ParagraphStyle(name='alignment', alignment=TA_RIGHT,
                                   parent=style['Normal'])

        # HEADER
        header_name = Paragraph(self.patient_name, style['Normal'])
        header_name.wrap(file_pdf.width, file_pdf.topMargin)
        header_name.drawOn(canvas_header, file_pdf.leftMargin, 270 * mm + (5 * mm))

        date_report = utcnow().to('local').format('dddd, DD - MMMM - YYYY', locale='es')
        date_report = date_report.replace('-', 'de')

        header_date = Paragraph(date_report, alignment)
        header_date.wrap(file_pdf.width, file_pdf.topMargin)
        header_date.drawOn(canvas_header, file_pdf.leftMargin, 270 * mm + (5 * mm))

        # FOOTER
        footer = Paragraph('Lectura Automática de Marcadores', style['Normal'])
        footer.wrap(file_pdf.width, file_pdf.bottomMargin)
        footer.drawOn(canvas_header, file_pdf.leftMargin, 15 * mm + (5 * mm))

        # DROP THE CANVAS
        canvas_header.restoreState()


def get_image_for_pdf(path_img, height=1 * mm):
    """
    :param path_img:
    :param height:
    :return Image(path, height=height, width=(height * aspect)):
    """

    img = utils.ImageReader(path_img)
    img_width, img_height = img.getSize()
    aspect = img_width / float(img_height)
    return Image(path_img, height=height, width=(height * aspect))


class ReportPdf(object):

    def __init__(self, name_pdf):
        super(ReportPdf, self).__init__()

        self.name_pdf = name_pdf
        self.styles = getSampleStyleSheet()
        self.width, self.height = A4

    def export_pdf(self, patient, db_dict, img_dict, conf, pages):
        """
        Export the assessment data to PDF.

        :param conf: assessment configuration parameter: angle and distance
        :param pages: boolean of assessment performed
        :param patient: patient's data
        :param db_dict: assessment data dictionary
        :param img_dict: image directory dictionary
        :return:
        """

        assessment_date = strftime('%d/%m/%Y')
        patient_name = patient.get_name()
        patient_age = patient.get_age()
        patient_gender = patient.get_gender()
        weight_kg = patient.get_weight_kg()
        height_cm = patient.get_height_cm()
        occupation = patient.get_occupation()

        db_anterior = db_dict['Anterior']
        db_posterior = db_dict['Posterior']
        db_lateral_r = db_dict['Lateral_d']

        img_anterior = '.\\final_anterior.jpg'
        img_posterior = '.\\final_posterior.jpg'
        img_lateral = '.\\final_lateral.jpg'

        anterior_img_dir = img_dict['Anterior']
        posterior_img_dir = img_dict['Posterior']
        lateral_r_img_dir = img_dict['Lateral_d']

        copyfile(img_anterior, anterior_img_dir)
        copyfile(img_posterior, posterior_img_dir)
        copyfile(img_lateral, lateral_r_img_dir)

        tolerance_angle = conf[0]
        tolerance_distance = conf[1]

        anterior_page = pages[0]
        posterior_page = pages[1]
        lateral_page = pages[2]

        # STYLES FORMAT

        PS = ParagraphStyle

        title_alignment = PS(name='title_alignment', alignment=TA_CENTER, fontSize=14,
                             leading=10, textColor=black,
                             parent=self.styles['Heading1'])

        main_paragraph = PS(name='main_paragraph', alignment=TA_LEFT, fontSize=10,
                            leading=8, textColor=black,
                            parent=self.styles['Heading1'])

        secondary_paragraph = PS(name='secondary_paragraph', alignment=TA_LEFT, fontSize=10,
                                 leading=16, textColor=black)

        data_table_style = (('BACKGROUND', (0, 0), (-1, 0), cornflowerblue),
                            ('TEXTCOLOR', (0, 0), (-1, 0), whitesmoke),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE', black),  # Centered and left-aligned text
                            ('INNERGRID', (0, 0), (-1, -1), 0.50, black),  # Internal lines
                            ('BOX', (0, 0), (-1, -1), 0.25, black),  # External lines
                            )

        results_table_style = (('BACKGROUND', (0, 0), (-1, 0), lightsteelblue),
                               ('TEXTCOLOR', (0, 0), (-1, 0), black),
                               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                               ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                               ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE', black),
                               ('INNERGRID', (0, 0), (-1, -1), 0.50, black),
                               ('BOX', (0, 0), (-1, -1), 0.25, black)
                               )

        data_table = Table((('Fecha', 'Nombre', 'Edad', 'Género', 'Talla [cm]', 'Peso [kg]', 'Ocupación'),
                            (assessment_date, patient_name, patient_age, patient_gender, height_cm, weight_kg,
                             occupation)), colWidths=(self.width - 100) / 7, hAlign='CENTER', style=data_table_style)

        data_table.argW[1] = 38 * mm  # Modify the cell widt

        lam_img_pdf = None
        try:
            lam_img_pdf = get_image_for_pdf('logo.png', height=100 * mm)
        except OSError:
            print('\nSin archivo "logo.png"')

        record = [Paragraph('Evaluación Postural', title_alignment), Spacer(1, 4 * mm), data_table,
                  lam_img_pdf]  # https://i.imgur.com/KRPTibG.png

        # CONFIGURATION

        conf_table = Table((('Ángulo de tolerancia', 'Distancia de toleracia'),
                            (f'{tolerance_angle} °', f'{tolerance_distance} cm')), colWidths=(self.width - 100) / 4,
                           hAlign='CENTER', style=data_table_style)

        record.append(conf_table)

        # DIAGNOSTIC
        if anterior_page:
            anterior_dg = db_anterior['diagnostic']
            record.append(Spacer(2, 4 * mm))
            record.append(Paragraph('VISTA ANTERIOR:', main_paragraph))
            record.append(Paragraph(f'Línea escapular descendida: {anterior_dg[0]}', secondary_paragraph))
            record.append(Paragraph(f'Línea pélvica descendida: {anterior_dg[1]}', secondary_paragraph))
            record.append(Paragraph(f'Cabeza inclinada: {anterior_dg[2]} con {anterior_dg[3]}°', secondary_paragraph))
            record.append(Paragraph(f'Cabeza rotada: {anterior_dg[4]}', secondary_paragraph))
            record.append(Paragraph(f'Rodillas: Derecha {anterior_dg[5]} {anterior_dg[6]}° ; '
                                    f'Izquierda {anterior_dg[7]} {anterior_dg[8]}°', secondary_paragraph))

        if posterior_page:
            posterior_dg = db_posterior['diagnostic']
            record.append(Spacer(2, 4 * mm))
            record.append(Paragraph('VISTA POSTERIOR:', main_paragraph))
            record.append(Paragraph(f'Rotación dorsal posterior: {posterior_dg[0]}', secondary_paragraph))
            record.append(Paragraph(f'Rotación pélvica posterior: {posterior_dg[1]}', secondary_paragraph))
            record.append(Paragraph(f'Pie izquierdo: {posterior_dg[2]}', secondary_paragraph))
            record.append(Paragraph(f'Pie derecho: {posterior_dg[3]}', secondary_paragraph))

        if lateral_page:
            lateral_r_dg = db_lateral_r['diagnostic']
            record.append(Spacer(2, 4 * mm))
            record.append(Paragraph('VISTA LATERAL DERECHA:', main_paragraph))
            record.append(Paragraph(f'Postura: {lateral_r_dg[0]}', secondary_paragraph))
            record.append(Paragraph(f'Proyección postural: {lateral_r_dg[1]}', secondary_paragraph))

        record.append(PageBreak())

        # ANTERIOR ASSESSMENT TABLE PAGE

        if anterior_page:
            df = db_anterior['table_1']

            anterior_table_part_1 = Table([df.columns.values.tolist()] + df.values.tolist(),
                                          colWidths=(self.width - 100) / 4, hAlign='LEFT',
                                          style=results_table_style)

            df = db_anterior['table_2']
            anterior_table_part_2 = Table([df.columns.values.tolist()] + df.values.tolist(),
                                          colWidths=(self.width - 100) / 4, hAlign='LEFT',
                                          style=results_table_style)

            df = db_anterior['table_3']

            anterior_table_part_3 = Table([df.columns.values.tolist()] + df.values.tolist(),
                                          colWidths=(self.width - 100) / 4, hAlign='LEFT',
                                          style=results_table_style)

            record.append(get_image_for_pdf(anterior_img_dir, height=100 * mm))
            record.append(Paragraph('Grados con respecto a la horizontal:', main_paragraph))
            record.append(Paragraph('El ángulo ideal debe ser <strong>0°</strong>.', secondary_paragraph))
            record.append(anterior_table_part_1)
            record.append(Paragraph('Distancia con respecto a la vertical:', main_paragraph))
            record.append(Paragraph('La distancia ideal debe ser <strong>0 cm</strong>.', secondary_paragraph))
            record.append(anterior_table_part_2)
            record.append(Paragraph('Grados de rotación de los pies:', main_paragraph))
            record.append(Paragraph('El ángulo ideal debe ser <strong>0°</strong>.', secondary_paragraph))
            record.append(anterior_table_part_3)
            record.append(PageBreak())

        # POSTERIOR ASSESSMENT TABLE PAGE

        if posterior_page:
            df = db_posterior['table_1']

            posterior_table_part_1 = Table([df.columns.values.tolist()] + df.values.tolist(),
                                           colWidths=(self.width - 100) / 4, hAlign='LEFT',
                                           style=results_table_style)

            df = db_posterior['table_2']

            posterior_table_part_2 = Table([df.columns.values.tolist()] + df.values.tolist(),
                                           colWidths=(self.width - 100) / 4, hAlign='LEFT',
                                           style=results_table_style)

            df = db_posterior['table_3']

            posterior_table_part_3 = Table([df.columns.values.tolist()] + df.values.tolist(),
                                           colWidths=(self.width - 100) / 4, hAlign='LEFT',
                                           style=results_table_style)

            record.append(get_image_for_pdf(posterior_img_dir, height=100 * mm))
            record.append(Paragraph('Grados con respecto a la horizontal:', main_paragraph))
            record.append(Paragraph('El ángulo ideal debe ser <strong>0°</strong>.', secondary_paragraph))
            record.append(posterior_table_part_1)
            record.append(Paragraph('Distancia con respecto a la vertical:', main_paragraph))
            record.append(Paragraph('La distancia ideal debe ser <strong>0 cm</strong>.', secondary_paragraph))
            record.append(posterior_table_part_2)
            record.append(Paragraph('Grados de rotación de los pies:', main_paragraph))
            record.append(Paragraph('El ángulo ideal debe ser <strong>0°</strong>.', secondary_paragraph))
            record.append(posterior_table_part_3)
            record.append(PageBreak())

        # LATERAL RIGHT ASSESSMENT TABLE PAGE

        if lateral_page:
            df = db_lateral_r['table_1']
            lateral_r_table_part_1 = Table([df.columns.values.tolist()] + df.values.tolist(),
                                           colWidths=(self.width - 100) / 4, hAlign='LEFT',
                                           style=results_table_style)

            df = db_lateral_r['table_2']

            lateral_r_table_part_2 = Table([df.columns.values.tolist()] + df.values.tolist(),
                                           colWidths=(self.width - 100) / 4, hAlign='LEFT',
                                           style=results_table_style)

            df = db_lateral_r['table_3']

            lateral_r_table_part_3 = Table([df.columns.values.tolist()] + df.values.tolist(),
                                           colWidths=(self.width - 100) / 4, hAlign='LEFT',
                                           style=results_table_style)

            record.append(get_image_for_pdf(lateral_r_img_dir, height=100 * mm))
            record.append(Paragraph('Grados con respecto a la vertical:', main_paragraph))
            record.append(Paragraph('El ángulo ideal debe ser <strong>0°</strong>.', secondary_paragraph))
            record.append(lateral_r_table_part_1)
            record.append(Paragraph('Grados con respecto a la horizontal:', main_paragraph))
            record.append(Paragraph('El ángulo normal entre los marcadores pélvicos anterior y posterior <strong>10°'
                                    '</strong>', secondary_paragraph))
            record.append(Paragraph('con una tolerancia de <strong>±5°</strong>.', secondary_paragraph))
            record.append(lateral_r_table_part_2)
            record.append(Paragraph('Distancia con respecto a la vertical:', main_paragraph))
            record.append(Paragraph('La distancia ideal debe ser <strong>0 cm</strong>.', secondary_paragraph))
            record.append(lateral_r_table_part_3)
            record.append(PageBreak())

        file_pdf = SimpleDocTemplate(self.name_pdf, leftMargin=50, rightMargin=50, pagesize=A4, title='Reporte PDF LAM',
                                     author='Youssef Abarca')

        header_and_footer = HeaderAndFooter(patient_name).print_header_and_footer

        try:
            file_pdf.build(record, onLaterPages=header_and_footer, canvasmaker=PageNumbering)
            record.clear()

            # +------------------------------------+
            return '\nReporte generado con éxito.'
        # +------------------------------------+
        except PermissionError:
            record.clear()
            # +--------------------------------------------+
            return '\nError inesperado: Permiso denegado.'
        # +--------------------------------------------+


def generate_report(patient, directory, data_dict, img_dict, conf, pages):
    """
    Generate the PDF report with its respective name

    :param patient: patient's data
    :param directory: save directory
    :param data_dict: assessment data dictionary
    :param img_dict:  image directory dictionary
    :param conf: assessment configuration parameter: angle and distance
    :param pages: boolean of assessment performed
    :return: name_pdf
    """

    name_pdf = patient.get_name() + '_' + strftime('%Y%m%d') + '_' + strftime('%H%M%S')
    report = ReportPdf(directory + name_pdf + '.pdf').export_pdf(patient, data_dict, img_dict, conf, pages)
    print(report)
    return name_pdf
