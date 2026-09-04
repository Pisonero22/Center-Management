"""Admin registrations, so the data can be managed without the public UI."""

from django.contrib import admin

from .models import Activity, Enrollment, Instructor, Member, Room


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    autocomplete_fields = ["member"]


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ["full_name", "email", "phone"]
    search_fields = ["full_name", "email"]


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ["full_name", "specialty"]
    search_fields = ["full_name", "specialty"]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "capacity", "location", "manager"]
    list_filter = ["location"]
    search_fields = ["name", "location"]


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "starts_at", "instructor", "main_room", "capacity"]
    list_filter = ["category", "instructor"]
    search_fields = ["name", "description"]
    date_hierarchy = "starts_at"
    inlines = [EnrollmentInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["member", "activity", "created_at"]
    list_filter = ["activity"]
