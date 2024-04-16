const URLS = {
    'service_list': () => `/service/`,
    'service_delete': (pk: number) => `/service/${pk}/delete`,
    'service_update': (pk: number) => `/service/${pk}/edit`,
    'service_detail': (pk: number) => `/service/${pk}`,
    'service_create': () => `/service/create`,
    'booking_list': () => `/booking/`,
    'booking_delete': (pk: number) => `/booking/${pk}/delete`,
    'booking_update': (pk: number) => `/booking/${pk}/edit`,
    'booking_detail': (pk: number) => `/booking/${pk}`,
    'booking_create': () => `/booking/create`,
    'invoice_send': (pk: number) => `/invoice/${pk}/send/`,
    'invoice_from_charges': () => `/invoice/from-charges/`,
    'invoice_email': (pk: number) => `/invoice/${pk}/email/`,
    'invoice_pdf': (pk: number) => `/invoice/${pk}/download/`,
    'invoice_list': () => `/invoice/`,
    'invoice_delete': (pk: number) => `/invoice/${pk}/delete`,
    'invoice_update': (pk: number) => `/invoice/${pk}/edit`,
    'invoice_detail': (pk: number) => `/invoice/${pk}`,
    'invoice_create': () => `/invoice/create`,
    'vet_list': () => `/vet/`,
    'vet_delete': (pk: number) => `/vet/${pk}/delete`,
    'vet_update': (pk: number) => `/vet/${pk}/edit`,
    'vet_detail': (pk: number) => `/vet/${pk}`,
    'vet_create': () => `/vet/create`,
    'pet_list': () => `/pet/`,
    'pet_delete': (pk: number) => `/pet/${pk}/delete`,
    'pet_update': (pk: number) => `/pet/${pk}/edit`,
    'pet_detail': (pk: number) => `/pet/${pk}`,
    'pet_create': (pk: number) => `/pet/create-for-customer/${pk}/`,
    'customer_uninvoiced_charges': (pk: number) => `/customer/${pk}/uninvoiced-charges/`,
    'customer_list': () => `/customer/`,
    'customer_delete': (pk: number) => `/customer/${pk}/delete`,
    'customer_update': (pk: number) => `/customer/${pk}/edit`,
    'customer_detail': (pk: number) => `/customer/${pk}`,
    'customer_create': () => `/customer/create`,
    'contact_create': (pk: number) => `/customer/${pk}/contact/create`,
    'invoice_action': (pk: number, action: string) => `/invoice/${pk}/action/${action}/`,
    'booking_calender_day': (year: number, month: number, day: number) => `/booking/calender/${year}/${month}/${day}`,
    'booking_calender_month': (year: number, month: number) => `/booking/calender/${year}/${month}/`,
    'booking_calender_year': (year: number) => `/booking/calender/${year}/`,
    'booking_action': (pk: number, action: string) => `/booking/${pk}/action/${action}/`,
    'dashboard': () => `/`,
};
export default URLS;
