import logging
import csv
import maya
import pydash

from django.conf import settings
from django.http import HttpResponse
from datetime import datetime
from django.utils.encoding import smart_str

import talentmap_api.bureau.services.available_bidders as bureau_services
import talentmap_api.fsbid.services.client as client_services

from talentmap_api.common.common_helpers import ensure_date, formatCSV

logger = logging.getLogger(__name__)

API_ROOT = settings.FSBID_API_URL


def get_available_bidders_stats(data):
    '''
    Returns Available Bidders status statistics
    '''
    stats = {
        'Bureau': {},  # code comes through, but only with the short name/acronym
        'Grade': {},
        'Location': {}, # need to verify what this should be, Location or Post?
        # 'Post': {},
        'Skill': {},
        'Status': {},
        'TED': {},
    }
    statsCount = {
        'Bureau': 0,
        'Grade': 0,
        'Location': 0,
        'Skill': 0,
        'Status': 0,
        'TED': 0,
    }
    # print('-------skills-------')
    # print(list(filter(None, data['results'][0]['skills'])))
    # # code as top level key and value
    # # description as name
    # print('-------skills-------')

    if data:
        # get stats for various fields
        for bidder in data['results']:
            if bidder['current_assignment']['position']['bureau_code'] not in stats['Bureau']:
                stats['Bureau'][bidder['current_assignment']['position']['bureau_code']] = {'name': f"{bidder['current_assignment']['position']['bureau_code']}", 'value': 0, 'color': '#112E51'}
            stats['Bureau'][bidder['current_assignment']['position']['bureau_code']]['value'] += 1
            statsCount['Bureau'] += 1

            if bidder['grade'] not in stats['Grade']:
                stats['Grade'][bidder['grade']] = {'name': f"Grade {bidder['grade']}", 'value': 0, 'color': '#112E51'}
            stats['Grade'][bidder['grade']]['value'] += 1
            statsCount['Grade'] += 1

            if bidder['pos_location'] not in stats['Location']:
                stats['Location'][bidder['pos_location']] = {'name': f"{bidder['pos_location']}", 'value': 0, 'color': '#112E51'}
            stats['Location'][bidder['pos_location']]['value'] += 1
            statsCount['Location'] += 1

            ted_key = smart_str(maya.parse(bidder['current_assignment']['end_date']).datetime().strftime('%m/%d/%Y'))
            if ted_key not in stats['TED']:
                stats['TED'][ted_key] = {'name': f"{ted_key}", 'value': 0, 'color': '#112E51'}
            stats['TED'][ted_key]['value'] += 1
            statsCount['TED'] += 1

            # const statsSum = Object.values(get(stats[0], selectedStat, {})[0].value).reduce((a, b) => a + b, 0);
            ab_status_key = bidder['available_bidder_details']['status']
            if bidder['available_bidder_details']['status'] is not None:
                if ab_status_key not in stats['Status']:
                    stats['Status'][ab_status_key] = {'name': f"{ab_status_key}", 'value': 0, 'color': '#112E51'}
                stats['Status'][ab_status_key]['value'] += 1
                statsCount['Status'] += 1

        print('statusCount')
        print(statsCount)
        print('statusCount')

            # skill_key = list(filter(None, bidder['skills']))
            # stats['Skill'][skill_key] = stats['Skill'].get(skill_key, 0) + 1
            # if stat['skills'] is not '':
            #     stats['Skill'][stat['skills']] += 1

        # color randomizer
        # number_of_colors = 8
        # color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
        # for i in range(number_of_colors)]

    biddersStats = {}
    for stat in stats:
        biddersStats[stat] = []
        for s in stats[stat]:
            biddersStats[stat].append(stats[stat][s])
    print('bidderStats')
    print(biddersStats)
    print('bidderStats')
    return {
        "stats": biddersStats,
        "statsCount": statsCount
    }


def get_available_bidders_csv(request):
    '''
    Returns csv format of Available Bidders list
    '''
    data = client_services.get_available_bidders(request.META['HTTP_JWT'], True, request.query_params, f"{request.scheme}://{request.get_host()}")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f"attachment; filename=Available_Bidders_{datetime.now().strftime('%Y_%m_%d_%H%M%S')}.csv"

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8'))

    # write the headers
    writer.writerow([
        smart_str(u"Name"),
        smart_str(u"Status"),
        smart_str(u"OC Bureau"),
        smart_str(u"OC Reason"),
        smart_str(u"Skills"),
        smart_str(u"Grade"),
        smart_str(u"Languages"),
        smart_str(u"TED"),
        smart_str(u"Organization"),
        smart_str(u"City"),
        smart_str(u"State"),
        smart_str(u"Country"),
        smart_str(u"CDO Name"),
        smart_str(u"CDO Email"),
        smart_str(u"Comments"),
        smart_str(u"Shared with Bureau"),
    ])
    fields_info = {
        "name": None,
        "status": {"path": 'available_bidder_details.status', },
        "skills": {"default": "No Skills listed", "description_and_code": True},
        "grade": None,
        "ted": {"path": 'current_assignment.end_date', },
        "oc_bureau": {"path": 'available_bidder_details.oc_bureau', },
        "oc_reason": {"path": 'available_bidder_details.oc_reason', },
        "org": {"path": 'current_assignment.position.organization', },
        "city": {"path": 'current_assignment.position.post.location.city', },
        "state": {"path": 'current_assignment.position.post.location.state', },
        "country": {"path": 'current_assignment.position.post.location.country', },
        "comments": {"path": 'available_bidder_details.comments', },
        "is_shared": {"path": 'available_bidder_details.is_shared', },
        "cdo_email": {"path": 'cdo.email', },
    }

    for record in data["results"]:
        languages = f'' if pydash.get(record, "languages") else "None listed"
        if languages is not "None listed":
            for language in record["languages"]:
                languages += f'{language["custom_description"]}, '
        languages = languages.rstrip(', ')

        cdo_name = f'{pydash.get(record, "cdo.last_name")}, {pydash.get(record, "cdo.first_name")}'

        fields = formatCSV(record, fields_info)

        try:
            ted = maya.parse(fields["ted"]).datetime().strftime('%m/%d/%Y')
        except:
            ted = 'None listed'
        writer.writerow([
            fields["name"],
            fields["status"],
            fields["oc_bureau"],
            fields["oc_reason"],
            fields["skills"],
            smart_str("=\"%s\"" % fields["grade"]),
            languages,
            ted,
            fields["org"],
            fields["city"],
            fields["state"],
            fields["country"],
            cdo_name,
            fields["cdo_email"],
            fields["comments"],
            fields["is_shared"],
        ])

    return response
