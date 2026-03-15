from django.shortcuts import render
from django.views import View


class DeanDownloadView(View):
    template_name = "pages/dean_download.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        faculty_csv = request.FILES.get("faculty_csv")
        bim_csv = request.FILES.get("bim_csv")

        if not faculty_csv or not bim_csv:
            return render(
                request,
                self.template_name,
                {"message": "Please upload both CSV files."},
            )

        # this need to be update by IURI later on
        message = (
            f"Received files: {faculty_csv.name} and {bim_csv.name}. "
            "Workbook generation logic will be connected next."
        )

        return render(request, self.template_name, {"message": message})
    
class FacultyPreferenceView(View):
    template_name = "pages/faculty_preference.html"
    def get(self, request):
        return render(request, self.template_name)
    
    ## Add additional code here for completion of form, postgres, etc
    ## will need a POST request