from uber.common import *

class Reminder:
    instances = OrderedDict()
    
    def __init__(self, model, subject, template, filter, sender=REGDESK_EMAIL, extra_data=None, cc=None, post_con=False):
        self.model, self.subject, self.template, self.sender = model, subject, template, sender
        self.cc = cc or []
        self.extra_data = extra_data or {}
        self.instances[subject] = self
        if post_con:
            self.filter = lambda x: POST_CON and filter(x)
        else:
            self.filter = lambda x: not POST_CON and filter(x)
    
    def __repr__(self):
        return '<{}: {!r}>'.format(self.__class__.__name__, self.subject)
    
    def prev(self, x, all_sent = None):
        if all_sent:
            return all_sent.get((x.__class__.__name__, x.id, self.subject))
        else:
            try:
                return Email.objects.get(model=x.__class__.__name__, fk_id=x.id, subject=self.subject)
            except:
                return None
    
    def should_send(self, x, all_sent = None):
        try:
            return not self.prev(x, all_sent) and self.filter(x)
        except:
            log.error('unexpected error', exc_info=True)
    
    def send(self, x, raise_errors = True):
        try:
            body = render('emails/' + self.template, dict({x.__class__.__name__.lower(): x}, **self.extra_data))
            format = 'text' if self.template.endswith('.txt') else 'html'
            send_email(self.sender, x.email, self.subject, body, format, model = x, cc=self.cc)
        except:
            log.error('error sending {!r} email to {}', self.subject, x.email, exc_info=True)
            if raise_errors:
                raise
    
    @staticmethod
    def send_all(raise_errors = False):
        attendees, groups = Group.everyone()
        models = {Attendee: attendees, Group: groups}
        all_sent = {(e.model, e.fk_id, e.subject): e for e in Email.objects.all()}
        if SEND_EMAILS and not AT_THE_CON:
            for rem in Reminder.instances.values():
                for x in models[rem.model]:
                    if x.email and rem.should_send(x, all_sent):
                        rem.send(x, raise_errors = raise_errors)

class StopsReminder(Reminder):
    def __init__(self, subject, template, filter, **kwargs):
        Reminder.__init__(self, Attendee, subject, template, lambda a: a.staffing and filter(a), STAFF_EMAIL, **kwargs)

class GuestReminder(Reminder):
    def __init__(self, subject, template, filter=lambda a: True, **kwargs):
        Reminder.__init__(self, Attendee, subject, template, lambda a: a.badge_type == GUEST_BADGE and filter(a), PANELS_EMAIL, **kwargs)

class DeptHeadReminder(Reminder):
    def __init__(self, subject, template, filter=lambda a: True, sender=STAFF_EMAIL, **kwargs):
        Reminder.__init__(self, Attendee, subject, template, lambda a: a.ribbon == DEPT_HEAD_RIBBON and len(a.assigned) == 1 and filter(a), sender, **kwargs)

class GroupReminder(Reminder):
    def __init__(self, subject, template, filter, **kwargs):
        Reminder.__init__(self, Group, subject, template, lambda g: not g.is_dealer and filter(g), REGDESK_EMAIL, **kwargs)

class MarketplaceReminder(Reminder):
    def __init__(self, subject, template, filter, **kwargs):
        Reminder.__init__(self, Group, subject, template, lambda g: g.is_dealer and filter(g), MARKETPLACE_EMAIL, **kwargs)

# see issue #173 about rewriting this
class SeasonSupporterReminder(Reminder):
    def __init__(self, event):
        Reminder.__init__(self, Attendee,
                                subject = 'Claim your {} tickets with your MAGFest Season Pass'.format(event['name']),
                                template = 'season_supporter_event_invite.txt',
                                filter = lambda a: a.amount_extra >= SEASON_LEVEL and before(event['deadline']),
                                extra_data = {'event': event})

before = lambda dt: bool(dt) and datetime.now() < dt
days_after = lambda days, dt: bool(dt) and (datetime.now() > dt + timedelta(days=days))
def days_before(days, dt, until=None):
    if dt:
        until = (dt - timedelta(days=until)) if until else dt
        return dt - timedelta(days=days) < datetime.now() < until


### WARNING - changing the email subject line for an email causes ALL of those emails to be re-sent!


MarketplaceReminder('Reminder to pay for your MAGFest Dealer registration', 'dealer_payment_reminder.txt',
                    lambda g: g.status == APPROVED and days_after(30, g.approved) and g.is_unpaid)

MarketplaceReminder('Your MAGFest Dealer registration is due in one week', 'dealer_payment_reminder.txt',
                    lambda g: g.status == APPROVED and days_before(7, DEALER_PAYMENT_DUE, 2) and g.is_unpaid)

MarketplaceReminder('Last chance to pay for your MAGFest Dealer registration', 'dealer_payment_reminder.txt',
                    lambda g: g.status == APPROVED and days_before(2, DEALER_PAYMENT_DUE) and g.is_unpaid)

MarketplaceReminder('MAGFest Dealer waitlist has been exhausted', 'dealer_waitlist_closing.txt',
                    lambda g: DEALER_WAITLIST_CLOSED and g.status == WAITLISTED)



MarketplaceReminder('Your MAGFest Dealer registration has been approved', 'dealer_approved.html',
                    lambda g: g.status == APPROVED)

Reminder(Attendee, 'MAGFest payment received', 'attendee_confirmation.html',
         lambda a: a.paid == HAS_PAID)

Reminder(Attendee, 'MAGFest group registration confirmed', 'attendee_confirmation.html',
         lambda a: a.group and a != a.group.leader and a.registered > datetime(2013, 11, 11))

Reminder(Group, 'MAGFest group payment received', 'group_confirmation.html',
         lambda g: g.amount_paid == g.total_cost)

Reminder(Attendee, 'MAGFest extra payment received', 'group_donation.txt',
         lambda a: a.paid == PAID_BY_GROUP and a.amount_extra and a.amount_paid == a.amount_extra)



Reminder(Attendee, 'MAGFest Badge Confirmation', 'badge_confirmation.txt',
         lambda a: a.placeholder and a.first_name and a.last_name
                                 and a.badge_type not in [GUEST_BADGE, STAFF_BADGE]
                                 and a.ribbon not in [PANELIST_RIBBON, VOLUNTEER_RIBBON])

Reminder(Attendee, 'MAGFest Panelist Badge Confirmation', 'panelist_confirmation.txt',
         lambda a: a.placeholder and a.first_name and a.last_name
                                 and (a.badge_type == GUEST_BADGE or a.ribbon == PANELIST_RIBBON),
         sender = PANELS_EMAIL)

StopsReminder('MAGFest Volunteer Badge Confirmation', 'volunteer_confirmation.txt',
              lambda a: a.placeholder and a.first_name and a.last_name
                                      and a.registered > PREREG_OPENING)

Reminder(Attendee, 'MAGFest Badge Confirmation Reminder', 'confirmation_reminder.txt',
         lambda a: days_after(7, a.registered) and a.placeholder and a.first_name and a.last_name)

Reminder(Attendee, 'Last Chance to Accept Your MAGFest Badge', 'confirmation_reminder.txt',
         lambda a: days_before(7, PLACEHOLDER_DEADLINE) and a.placeholder and a.first_name and a.last_name)



StopsReminder('Want to staff MAGFest again?', 'imported_staffer.txt',
              lambda a: a.placeholder and a.badge_type == STAFF_BADGE and a.registered < PREREG_OPENING)

StopsReminder('MAGFest shifts available', 'shifts_created.txt',
              lambda a: state.AFTER_SHIFTS_CREATED and a.takes_shifts)

StopsReminder('Reminder to sign up for MAGFest shifts', 'shift_reminder.txt',
              lambda a: days_after(30, max(a.registered, SHIFTS_CREATED))
                    and state.AFTER_SHIFTS_CREATED and not PREREG_CLOSED and a.takes_shifts and not a.hours)

StopsReminder('Last chance to sign up for MAGFest shifts', 'shift_reminder.txt',
              lambda a: days_before(10, EPOCH) and state.AFTER_SHIFTS_CREATED and not PREREG_CLOSED
                                               and a.takes_shifts and not a.hours)

StopsReminder('Still want to volunteer at MAGFest?', 'volunteer_check.txt',
              lambda a: days_before(5, UBER_TAKEDOWN) and a.ribbon == VOLUNTEER_RIBBON
                                                      and a.takes_shifts and a.weighted_hours == 0)

StopsReminder('MAGCon - the convention to plan MAGFest!', 'magcon.txt',
              lambda a: days_before(14, MAGCON))


StopsReminder('Want volunteer hotel room space at MAGFest?', 'hotel_rooms.txt',
              lambda a: days_before(45, ROOM_DEADLINE, 14) and state.AFTER_SHIFTS_CREATED and a.hotel_eligible)

StopsReminder('Reminder to sign up for MAGFest hotel room space', 'hotel_reminder.txt',
              lambda a: days_before(14, ROOM_DEADLINE, 2) and a.hotel_eligible and not a.hotel_requests)

StopsReminder('Last chance to sign up for MAGFest hotel room space', 'hotel_reminder.txt',
              lambda a: days_before(2, ROOM_DEADLINE) and a.hotel_eligible and not a.hotel_requests)

StopsReminder('Reminder to meet your MAGFest hotel room requirements', 'hotel_hours.txt',
              lambda a: days_before(14, UBER_TAKEDOWN, 7) and a.hotel_shifts_required and a.weighted_hours < 30)

StopsReminder('Final reminder to meet your MAGFest hotel room requirements', 'hotel_hours.txt',
              lambda a: days_before(7, UBER_TAKEDOWN) and a.hotel_shifts_required and a.weighted_hours < 30)

StopsReminder('Last chance to personalize your MAGFest badge', 'personalized_badge_reminder.txt',
              lambda a: days_before(7, PRINTED_BADGE_DEADLINE) and a.badge_type == STAFF_BADGE and a.placeholder)

Reminder(Attendee, 'Personalized MAGFest badges will be ordered next week', 'personalized_badge_deadline.txt',
         lambda a: days_before(7, PRINTED_BADGE_DEADLINE) and a.badge_type in [STAFF_BADGE, SUPPORTER_BADGE] and not a.placeholder)

StopsReminder('MAGFest Tech Ops volunteering', 'techops.txt',
              lambda a: TECH_OPS in a.requested_depts_ints and TECH_OPS not in a.assigned)

StopsReminder('MAGFest Chipspace volunteering', 'chipspace.txt',
              lambda a: (JAMSPACE in a.requested_depts_ints or JAMSPACE in a.assigned) and CHIPSPACE not in a.assigned)

StopsReminder('MAGFest Chipspace shifts', 'chipspace_trusted.txt',
              lambda a: CHIPSPACE in a.assigned and a.trusted)

StopsReminder('MAGFest Chipspace', 'chipspace_untrusted.txt',
              lambda a: a.has_shifts_in(CHIPSPACE) and not a.trusted)

StopsReminder('MAGFest food prep volunteering', 'food_interest.txt',
              lambda a: FOOD_PREP in a.requested_depts_ints and not a.assigned_depts)

StopsReminder('MAGFest food prep rules', 'food_volunteers.txt',
              lambda a: a.has_shifts_in(FOOD_PREP) and not a.trusted)

StopsReminder('MAGFest message from Chef', 'food_trusted_staffers.txt',
              lambda a: a.has_shifts_in(FOOD_PREP) and a.trusted)

StopsReminder('MAGFest Volunteer Food', 'volunteer_food_info.txt',
              lambda a: days_before(7, UBER_TAKEDOWN))

Reminder(Attendee, 'Want to help run MAGFest poker tournaments?', 'poker.txt',
         lambda a: a.has_shifts_in(TABLETOP), sender='tabletop@magfest.org')


DeptHeadReminder('Assign MAGFest hotel rooms for your department', 'room_assignments.txt',
                 lambda a: days_before(45, ROOM_DEADLINE))

DeptHeadReminder('Reminder for MAGFest department heads to double-check their staffers', 'dept_head_rooms.txt',
                 lambda a: days_before(45, ROOM_DEADLINE))

DeptHeadReminder('Last reminder for MAGFest department heads to double-check their staffers', 'dept_head_rooms.txt',
                 lambda a: days_before(7, ROOM_DEADLINE))

DeptHeadReminder('Last chance for Department Heads to get Staff badges for your people', 'dept_head_badges.txt',
                 lambda a: days_before(7, PRINTED_BADGE_DEADLINE))

DeptHeadReminder('Need help with MAGFest setup/teardown?', 'dept_head_setup_teardown.txt',
                 lambda a: days_before(14, ROOM_DEADLINE))

DeptHeadReminder('Department Ribbons', 'dept_head_ribbons.txt',
                 lambda a: days_before(1, ROOM_DEADLINE),
                 sender=REGDESK_EMAIL)

DeptHeadReminder('Final list of MAGFest hotel allocations for your department', 'hotel_list.txt',
                 lambda a: days_before(1, ROOM_DEADLINE + timedelta(days=6)))

DeptHeadReminder('Unconfirmed MAGFest staffers in your department', 'dept_placeholders.txt',
                 lambda a: days_before(21, UBER_TAKEDOWN))


GroupReminder('Reminder to pre-assign MAGFest group badges', 'group_preassign_reminder.txt',
              lambda g: days_after(30, g.registered) and state.BEFORE_GROUP_REG_TAKEDOWN and g.unregistered_badges)

Reminder(Group, 'Last chance to pre-assign MAGFest group badges', 'group_preassign_reminder.txt',
         lambda g: state.AFTER_GROUP_REG_TAKEDOWN and g.unregistered_badges and (not g.is_dealer or g.status == APPROVED))



Reminder(Attendee, 'MAGFest parental consent form reminder', 'under_18_reminder.txt',
         lambda a: a.age_group == UNDER_18 and days_before(7, EPOCH))

GuestReminder('MAGFest food for guests', 'guest_food.txt')

GuestReminder('MAGFest hospitality suite information', 'guest_food_info.txt')

Reminder(Attendee, 'MAGFest schedule, maps, and other FAQs', 'precon_faqs.html', lambda a: days_before(7, EPOCH))


DeptHeadReminder('MAGFest staffers need to be marked and rated', 'postcon_hours.txt', post_con=True)


# see issue #173 about rewriting this
#for _event in SEASON_EVENTS.values():
#    SeasonSupporterReminder(_event)


@all_renderable(PEOPLE)
class Root:
    def index(self):
        raise HTTPRedirect('by_sent')
    
    def by_sent(self, page='1'):
        emails = Email.objects.order_by('-when')
        return {
            'page': page,
            'emails': get_page(page, emails),
            'count': emails.count()
        }
    
    def sent(self, **params):
        return {'emails': Email.objects.filter(**params).order_by('when')}
